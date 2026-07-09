# services/storage/timescale.py

"""
TimescaleClient — asyncpg pool para TimescaleDB.

Hypertable: protocol_metrics (timestamp, protocol_id, metric_name)
Schema definido em services/storage/architecture.py.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

import asyncpg
import structlog

log = structlog.get_logger(__name__)

# ── SQL ──────────────────────────────────────────────────────────────────────

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS protocol_metrics (
    timestamp       TIMESTAMPTZ NOT NULL,
    protocol_id     TEXT NOT NULL,
    chain_id        TEXT,
    metric_name     TEXT NOT NULL,
    value_numeric   DOUBLE PRECISION,
    value_json      JSONB,
    source_id       TEXT NOT NULL,
    confidence      REAL DEFAULT 1.0,
    PRIMARY KEY (timestamp, protocol_id, metric_name)
);
"""

_CREATE_HYPERTABLE = """
SELECT create_hypertable(
    'protocol_metrics',
    'timestamp',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);
"""

_UPSERT = """
INSERT INTO protocol_metrics
    (timestamp, protocol_id, chain_id, metric_name, value_numeric, value_json, source_id, confidence)
VALUES
    ($1, $2, $3, $4, $5, $6, $7, $8)
ON CONFLICT (timestamp, protocol_id, metric_name) DO UPDATE SET
    chain_id      = EXCLUDED.chain_id,
    value_numeric = EXCLUDED.value_numeric,
    value_json    = EXCLUDED.value_json,
    source_id     = EXCLUDED.source_id,
    confidence    = EXCLUDED.confidence;
"""

_GET_LATEST = """
SELECT value_numeric
FROM protocol_metrics
WHERE protocol_id = $1
  AND metric_name = $2
ORDER BY timestamp DESC
LIMIT 1;
"""


# ── Client ────────────────────────────────────────────────────────────────────

class TimescaleClient:
    """
    Cliente asyncpg para TimescaleDB.

    Usage:
        client = TimescaleClient(dsn)
        await client.connect()
        await client.ensure_schema()
        # ... use client ...
        await client.close()
    """

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self._pool: asyncpg.Pool | None = None

    # ── Lifecycle ──

    async def connect(self, min_size: int = 2, max_size: int = 10) -> None:
        """Cria o pool de conexões asyncpg."""
        log.info("timescale.connecting", dsn=self._dsn.split("@")[-1])
        self._pool = await _create_pool_with_retry(
            self._dsn, min_size=min_size, max_size=max_size
        )
        log.info("timescale.connected", min=min_size, max=max_size)

    async def close(self) -> None:
        """Fecha o pool de conexões."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            log.info("timescale.closed")

    # ── Schema ──

    async def ensure_schema(self) -> None:
        """
        Cria a tabela e hypertable se não existirem.
        Idempotente — seguro chamar múltiplas vezes.
        """
        pool = self._get_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(_CREATE_TABLE)
                log.debug("timescale.table_ensured", table="protocol_metrics")
                try:
                    await conn.execute(_CREATE_HYPERTABLE)
                    log.debug("timescale.hypertable_ensured")
                except asyncpg.exceptions.DuplicateTableError:
                    # Hypertable já existe — ignorar
                    pass
                except Exception as exc:
                    # create_hypertable falha com mensagem específica se já existe,
                    # mas if_not_exists => TRUE deve prevenir isso
                    log.warning("timescale.hypertable_skip", reason=str(exc))

    # ── Write ──

    async def upsert_metric(
        self,
        timestamp: datetime,
        protocol_id: str,
        metric_name: str,
        value_numeric: float | None,
        value_json: dict | None = None,
        source_id: str = "defillama",
        chain_id: str | None = None,
        confidence: float = 1.0,
    ) -> None:
        """Insere ou atualiza uma métrica individual."""
        pool = self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                _UPSERT,
                timestamp,
                protocol_id,
                chain_id,
                metric_name,
                value_numeric,
                value_json,
                source_id,
                confidence,
            )

    async def upsert_metrics_batch(self, rows: list[dict]) -> int:
        """
        Insere ou atualiza um batch de métricas.

        Args:
            rows: Lista de dicts com as mesmas chaves de upsert_metric.

        Returns:
            Número de linhas inseridas/atualizadas.
        """
        if not rows:
            return 0

        pool = self._get_pool()
        records = [_row_to_record(r) for r in rows]

        async with pool.acquire() as conn:
            await conn.executemany(_UPSERT, records)

        count = len(records)
        log.debug("timescale.batch_upserted", rows=count)
        return count

    # ── Read ──

    async def get_latest(
        self,
        protocol_id: str,
        metric_name: str,
    ) -> float | None:
        """Retorna o valor numérico mais recente de uma métrica."""
        pool = self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(_GET_LATEST, protocol_id, metric_name)
        return row["value_numeric"] if row else None

    # ── Internal ──

    def _get_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            raise RuntimeError("TimescaleClient: chame connect() primeiro")
        return self._pool


# ── Helpers ──────────────────────────────────────────────────────────────────

def _row_to_record(row: dict) -> tuple[Any, ...]:
    """Converte dict de kwargs para tuple na ordem do _UPSERT."""
    return (
        row["timestamp"],
        row["protocol_id"],
        row.get("chain_id"),
        row["metric_name"],
        row.get("value_numeric"),
        row.get("value_json"),
        row.get("source_id", "defillama"),
        row.get("confidence", 1.0),
    )


async def _create_pool_with_retry(
    dsn: str,
    min_size: int,
    max_size: int,
    max_retries: int = 5,
) -> asyncpg.Pool:
    """
    Cria pool com retry exponencial em TooManyConnectionsError.
    Também aguarda o banco subir (útil em docker-compose).
    """
    delay = 1.0
    last_exc: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            return await asyncpg.create_pool(
                dsn=dsn,
                min_size=min_size,
                max_size=max_size,
                command_timeout=30,
            )
        except asyncpg.TooManyConnectionsError as exc:
            last_exc = exc
            log.warning(
                "timescale.too_many_connections",
                attempt=attempt,
                retry_in=delay,
            )
        except (ConnectionRefusedError, OSError) as exc:
            last_exc = exc
            log.warning(
                "timescale.connection_refused",
                attempt=attempt,
                retry_in=delay,
            )
        await asyncio.sleep(delay)
        delay = min(delay * 2, 30.0)

    raise RuntimeError(
        f"TimescaleDB: falhou após {max_retries} tentativas — {last_exc}"
    )
