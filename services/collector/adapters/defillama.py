# services/collector/adapters/defillama.py

"""
DefiLlamaAdapter — coleta dados da API pública da DeFiLlama.

Sem autenticação. Rate limit razoável (initial_delay_ms=300).
Tier 2 — REST API.

Uso:
    adapter = DefiLlamaAdapter()
    async for dp in adapter.collect({"endpoint": "protocols"}):
        rows = engine.normalize(dp)
        await client.upsert_metrics_batch(rows)
"""

from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from typing import AsyncIterator

import httpx
import structlog

from services.collector.adapters.base import BaseAdapter, RawDataPoint
from services.collector.adapters.rate_limited_mixin import RateLimitedMixin

log = structlog.get_logger(__name__)

_SOURCE_ID = "defillama"
_SOURCE_TIER = 2
_SCHEMA_VERSION = "defillama_v2"


class DefiLlamaAdapter(RateLimitedMixin, BaseAdapter):
    """
    Adapter REST para a DeFiLlama API pública.

    Endpoints suportados:
        protocols   — /v2/protocols    (lista completa, ~3000 protocolos)
        protocol    — /protocol/{slug} (detalhe de um protocolo)
        fees        — /overview/fees   (fees e revenue)
        hacks       — /hacks           (histórico de exploits)
        raises      — /raises          (fundraising rounds)
        yields      — /pools           (yield universe)
    """

    BASE_URL = "https://api.llama.fi"

    ENDPOINTS = {
        "protocols":  "/v2/protocols",
        "protocol":   "/protocol/{slug}",
        "fees":       "/overview/fees",
        "hacks":      "/hacks",
        "raises":     "/raises",
        "yields":     "/pools",
    }

    def __init__(self) -> None:
        self.__init_rate_limiter__(
            initial_delay_ms=300.0,
            min_delay_ms=100.0,
            max_delay_ms=10_000.0,
            failure_threshold=5,
            timeout_seconds=60.0,
        )
        self._client: httpx.AsyncClient | None = None

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                timeout=httpx.Timeout(30.0, connect=10.0),
                headers={"Accept": "application/json"},
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    # ── BaseAdapter contract ───────────────────────────────────────────────────

    async def health_check(self) -> bool:
        try:
            client = await self._get_client()
            resp = await client.get("/v2/protocols", timeout=5.0)
            return resp.status_code == 200
        except Exception:
            return False

    async def validate_response(self, data: RawDataPoint) -> bool:
        payload = data.raw_payload
        endpoint = data.metadata.get("endpoint", "")
        if endpoint == "protocols":
            return isinstance(payload, list) and len(payload) > 0
        if endpoint == "protocol":
            return isinstance(payload, dict) and "name" in payload
        return payload is not None

    def get_rate_limit_config(self) -> dict:
        return self.get_rate_limit_stats()

    def get_schema(self) -> dict:
        return {"source_id": _SOURCE_ID, "tier": _SOURCE_TIER}

    # ── collect() ─────────────────────────────────────────────────────────────

    async def collect(self, params: dict) -> AsyncIterator[RawDataPoint]:
        """
        Async generator de RawDataPoints.

        params["endpoint"] seleciona o método:
            {"endpoint": "protocols"}                  → collect_all_protocols()
            {"endpoint": "protocol", "slug": "uniswap"} → collect_protocol_deep(slug)
            {"endpoint": "fees"}                       → collect_fees()
            {"endpoint": "hacks"}                      → collect_hacks()
            {"endpoint": "raises"}                     → collect_raises()
            {"endpoint": "yields"}                     → collect_yields()
        """
        endpoint = params.get("endpoint", "protocols")
        slug = params.get("slug")

        if endpoint == "protocols":
            async for dp in self.collect_all_protocols():
                yield dp
        elif endpoint == "protocol":
            if not slug:
                raise ValueError("collect(protocol): slug obrigatório")
            async for dp in self.collect_protocol_deep(slug):
                yield dp
        elif endpoint == "fees":
            async for dp in self.collect_fees():
                yield dp
        elif endpoint == "hacks":
            async for dp in self.collect_hacks():
                yield dp
        elif endpoint == "raises":
            async for dp in self.collect_raises():
                yield dp
        elif endpoint == "yields":
            async for dp in self.collect_yields():
                yield dp
        else:
            raise ValueError(f"DefiLlamaAdapter: endpoint desconhecido: {endpoint!r}")

    # ── Endpoint methods ───────────────────────────────────────────────────────

    async def collect_all_protocols(self) -> AsyncIterator[RawDataPoint]:
        """GET /v2/protocols — lista ~3000 protocolos com TVL atual."""
        dp = await self._fetch_endpoint(
            path=self.ENDPOINTS["protocols"],
            endpoint_key="protocols",
        )
        if dp:
            yield dp

    async def collect_protocol_deep(self, slug: str) -> AsyncIterator[RawDataPoint]:
        """GET /protocol/{slug} — TVL por chain, token info, etc."""
        path = self.ENDPOINTS["protocol"].format(slug=slug)
        dp = await self._fetch_endpoint(
            path=path,
            endpoint_key="protocol",
            extra_meta={"slug": slug},
        )
        if dp:
            yield dp

    async def collect_fees(self) -> AsyncIterator[RawDataPoint]:
        """GET /overview/fees — fees e revenue de todos os protocolos."""
        dp = await self._fetch_endpoint(
            path=self.ENDPOINTS["fees"],
            endpoint_key="fees",
        )
        if dp:
            yield dp

    async def collect_hacks(self) -> AsyncIterator[RawDataPoint]:
        """GET /hacks — histórico de exploits."""
        dp = await self._fetch_endpoint(
            path=self.ENDPOINTS["hacks"],
            endpoint_key="hacks",
        )
        if dp:
            yield dp

    async def collect_raises(self) -> AsyncIterator[RawDataPoint]:
        """GET /raises — fundraising rounds."""
        dp = await self._fetch_endpoint(
            path=self.ENDPOINTS["raises"],
            endpoint_key="raises",
        )
        if dp:
            yield dp

    async def collect_yields(self) -> AsyncIterator[RawDataPoint]:
        """GET /pools — pool yields universe."""
        dp = await self._fetch_endpoint(
            path=self.ENDPOINTS["yields"],
            endpoint_key="yields",
        )
        if dp:
            yield dp

    # ── Internal ──────────────────────────────────────────────────────────────

    async def _fetch_endpoint(
        self,
        path: str,
        endpoint_key: str,
        extra_meta: dict | None = None,
    ) -> RawDataPoint | None:
        """
        Executa request com _acquire() + _call_protected() + _report().
        Retorna RawDataPoint ou None em caso de erro.
        """
        url = f"{self.BASE_URL}{path}"
        log.debug("defillama.fetch", endpoint=endpoint_key, url=url)

        await self._acquire()
        t0 = time.monotonic()

        try:
            response = await self._call_protected(self._do_get, path)
        except Exception as exc:
            log.error("defillama.fetch_error", endpoint=endpoint_key, exc=str(exc))
            await self._report(503, (time.monotonic() - t0) * 1000)
            return None

        elapsed_ms = (time.monotonic() - t0) * 1000
        await self._report(response.status_code, elapsed_ms)

        if response.status_code != 200:
            log.warning(
                "defillama.bad_status",
                endpoint=endpoint_key,
                status=response.status_code,
            )
            return None

        try:
            payload = response.json()
        except Exception as exc:
            log.error("defillama.parse_error", endpoint=endpoint_key, exc=str(exc))
            return None

        content_hash = _sha256(payload)
        now = datetime.now(tz=timezone.utc)

        meta: dict = {"endpoint": endpoint_key}
        if extra_meta:
            meta.update(extra_meta)

        return RawDataPoint(
            source_id=_SOURCE_ID,
            source_tier=_SOURCE_TIER,
            collection_timestamp=now,
            data_timestamp=now,
            raw_payload=payload,
            content_hash=content_hash,
            schema_version=_SCHEMA_VERSION,
            collection_method="rest_api",
            url_or_endpoint=url,
            http_status=response.status_code,
            response_headers=dict(response.headers),
            metadata=meta,
        )

    async def _do_get(self, path: str) -> httpx.Response:
        """Executa o GET — chamado via _call_protected."""
        client = await self._get_client()
        return await client.get(path)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _sha256(payload: dict | list | str) -> str:
    """SHA-256 do payload serializado (sort_keys para determinismo)."""
    if isinstance(payload, (dict, list)):
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    else:
        raw = str(payload)
    return hashlib.sha256(raw.encode()).hexdigest()
