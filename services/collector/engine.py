# services/collector/engine.py

"""
CollectorEngine — orchestrator do pipeline de coleta contínua.

Agenda adapters, normaliza, deduplica e persiste no TimescaleDB.
Cada adapter corre em task assíncrona isolada — falha de um não afeta os outros.

Uso:
    engine = CollectorEngine(dsn="postgresql://...")
    await engine.setup()
    engine.schedule(DefiLlamaAdapter(), {"endpoint": "protocols"}, interval=3600)
    engine.schedule(CoinGeckoAdapter(),  {"endpoint": "markets"},   interval=300)
    await engine.run_forever()
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

import structlog

from services.collector.adapters.base import BaseAdapter, RawDataPoint
from services.collector.adapters.coingecko import CoinGeckoAdapter
from services.collector.adapters.defillama import DefiLlamaAdapter
from services.collector.adapters.ethereum_rpc import EthereumRPCAdapter
from services.collector.adapters.snapshot import SnapshotAdapter
from services.collector.adapters.thegraph import TheGraphAdapter
from services.normalizer.engine import NormalizerEngine
from services.storage.timescale import TimescaleClient

log = structlog.get_logger(__name__)


# ── Job ───────────────────────────────────────────────────────────────────────

@dataclass
class CollectorJob:
    """Define um adapter + params + intervalo de coleta."""
    adapter: BaseAdapter
    params: dict
    interval_seconds: float
    name: str = ""
    _next_run: float = field(default_factory=time.monotonic, init=False)

    def __post_init__(self) -> None:
        if not self.name:
            source = type(self.adapter).__name__
            endpoint = self.params.get("endpoint", "?")
            self.name = f"{source}:{endpoint}"

    def is_due(self) -> bool:
        return time.monotonic() >= self._next_run

    def reschedule(self) -> None:
        self._next_run = time.monotonic() + self.interval_seconds


# ── Engine ────────────────────────────────────────────────────────────────────

class CollectorEngine:
    """
    Orchestrator assíncrono de coleta contínua.

    Características:
    - Isolamento por job: erro num adapter não para os outros
    - Deduplicação in-memory por content_hash (MVP — Redis na FASE 3)
    - Normalização via NormalizerEngine
    - Persistência via TimescaleClient (asyncpg pool)
    - Tick a cada segundo para checagem de jobs prontos
    """

    def __init__(self, dsn: str, max_dedup_cache: int = 100_000) -> None:
        self._dsn = dsn
        self._jobs: list[CollectorJob] = []
        self._storage: TimescaleClient | None = None
        self._normalizer = NormalizerEngine()
        self._seen_hashes: set[str] = set()
        self._max_dedup_cache = max_dedup_cache

        self._stats: dict[str, int] = {
            "rows_total": 0,
            "dps_total": 0,
            "dps_deduped": 0,
            "errors_total": 0,
        }

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    async def setup(self) -> None:
        """Conecta ao TimescaleDB e cria schema."""
        self._storage = TimescaleClient(self._dsn)
        await self._storage.connect()
        await self._storage.ensure_schema()
        log.info("collector.engine.ready", dsn=self._dsn.split("@")[-1])

    async def teardown(self) -> None:
        """Fecha conexões."""
        if self._storage:
            await self._storage.close()
        for job in self._jobs:
            if hasattr(job.adapter, "close"):
                await job.adapter.close()
        log.info("collector.engine.stopped")

    # ── Job registration ───────────────────────────────────────────────────────

    def schedule(
        self,
        adapter: BaseAdapter,
        params: dict,
        interval_seconds: float,
        name: str = "",
    ) -> None:
        """Registra um adapter para coleta periódica."""
        job = CollectorJob(
            adapter=adapter,
            params=params,
            interval_seconds=interval_seconds,
            name=name,
        )
        self._jobs.append(job)
        log.info("collector.job.registered", name=job.name, interval=interval_seconds)

    # ── Main loop ──────────────────────────────────────────────────────────────

    async def run_forever(self) -> None:
        """
        Loop principal — tick a cada segundo, dispara jobs prontos em paralelo.
        Roda até receber KeyboardInterrupt ou CancelledError.
        """
        if not self._storage:
            raise RuntimeError("CollectorEngine: chame setup() primeiro")

        log.info("collector.engine.starting", jobs=len(self._jobs))

        try:
            while True:
                due = [j for j in self._jobs if j.is_due()]
                if due:
                    await asyncio.gather(
                        *(self._run_job(job) for job in due),
                        return_exceptions=True,
                    )
                await asyncio.sleep(1.0)
        except (KeyboardInterrupt, asyncio.CancelledError):
            log.info("collector.engine.stopping", **self._stats)
        finally:
            await self.teardown()

    # ── Job execution ──────────────────────────────────────────────────────────

    async def _run_job(self, job: CollectorJob) -> None:
        """Executa um job: coleta → normaliza → deduplica → persiste."""
        job.reschedule()
        log.debug("collector.job.start", name=job.name)
        t0 = time.monotonic()

        try:
            dp_count = 0
            row_count = 0

            async for dp in job.adapter.collect(job.params):
                dp_count += 1
                self._stats["dps_total"] += 1

                if self._is_duplicate(dp):
                    self._stats["dps_deduped"] += 1
                    continue

                self._mark_seen(dp)
                rows = self._normalizer.normalize(dp)

                if rows and self._storage:
                    inserted = await self._storage.upsert_metrics_batch(rows)
                    row_count += inserted
                    self._stats["rows_total"] += inserted

            log.info(
                "collector.job.done",
                name=job.name,
                dps=dp_count,
                rows=row_count,
                elapsed_s=round(time.monotonic() - t0, 2),
            )

        except Exception as exc:
            self._stats["errors_total"] += 1
            log.error(
                "collector.job.error",
                name=job.name,
                exc=str(exc),
                exc_type=type(exc).__name__,
            )

    # ── Deduplication ──────────────────────────────────────────────────────────

    def _is_duplicate(self, dp: RawDataPoint) -> bool:
        return dp.content_hash in self._seen_hashes

    def _mark_seen(self, dp: RawDataPoint) -> None:
        if len(self._seen_hashes) >= self._max_dedup_cache:
            to_remove = list(self._seen_hashes)[: self._max_dedup_cache // 2]
            for h in to_remove:
                self._seen_hashes.discard(h)
        self._seen_hashes.add(dp.content_hash)

    def get_stats(self) -> dict[str, Any]:
        return {**self._stats, "jobs": len(self._jobs), "dedup_cache": len(self._seen_hashes)}


# ── Default pipeline ──────────────────────────────────────────────────────────

def build_default_pipeline(dsn: str) -> CollectorEngine:
    """
    Monta o pipeline padrão FASE 1+2+3:

    FASE 1+2 — REST APIs:
        DefiLlama protocols  — a cada 1h
        DefiLlama fees       — a cada 1h
        DefiLlama hacks      — a cada 6h
        CoinGecko markets    — a cada 5min (top 250)
        CoinGecko global     — a cada 5min

    FASE 3 — On-chain + GraphQL:
        Ethereum block       — a cada 12s  (tempo médio de bloco)
        Ethereum fee_history — a cada 1min
        Snapshot proposals   — a cada 10min (governance ativa)
        Snapshot spaces      — a cada 1h   (metadados de spaces)
        TheGraph Uniswap v3  — a cada 5min (pools TVL/volume)
    """
    engine = CollectorEngine(dsn=dsn)

    # ── FASE 1+2 ──
    defillama = DefiLlamaAdapter()
    engine.schedule(defillama, {"endpoint": "protocols"}, interval_seconds=3600,  name="defillama:protocols")
    engine.schedule(defillama, {"endpoint": "fees"},      interval_seconds=3600,  name="defillama:fees")
    engine.schedule(defillama, {"endpoint": "hacks"},     interval_seconds=21600, name="defillama:hacks")

    coingecko = CoinGeckoAdapter()
    engine.schedule(coingecko, {"endpoint": "markets", "per_page": 250}, interval_seconds=300, name="coingecko:markets")
    engine.schedule(coingecko, {"endpoint": "global"},                    interval_seconds=300, name="coingecko:global")

    # ── FASE 3 ──
    ethereum = EthereumRPCAdapter()
    engine.schedule(ethereum, {"endpoint": "block"},       interval_seconds=12,  name="ethereum:block")
    engine.schedule(ethereum, {"endpoint": "fee_history"}, interval_seconds=60,  name="ethereum:fee_history")

    snapshot = SnapshotAdapter()
    engine.schedule(snapshot, {"endpoint": "proposals", "state": "active"},  interval_seconds=600,  name="snapshot:proposals_active")
    engine.schedule(snapshot, {"endpoint": "spaces"},                        interval_seconds=3600, name="snapshot:spaces")

    thegraph = TheGraphAdapter()
    engine.schedule(
        thegraph,
        {
            "endpoint": "query",
            "subgraph": "uniswap/uniswap-v3",
            "query": "{ pools(first: 100, orderBy: volumeUSD, orderDirection: desc) { id feeTier totalValueLockedUSD volumeUSD txCount } }",
        },
        interval_seconds=300,
        name="thegraph:uniswap_v3_pools",
    )

    return engine


# ── Entrypoint ────────────────────────────────────────────────────────────────

async def _main() -> None:
    import os
    dsn = os.environ.get(
        "TIMESCALE_URL",
        "postgresql://chainscope:chainscope@localhost:5432/chainscope",
    )
    pipeline = build_default_pipeline(dsn)
    await pipeline.setup()
    await pipeline.run_forever()


if __name__ == "__main__":
    asyncio.run(_main())
