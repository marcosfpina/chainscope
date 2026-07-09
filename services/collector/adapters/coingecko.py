# services/collector/adapters/coingecko.py

"""
CoinGeckoAdapter — coleta preços e market data da API pública CoinGecko.

Free tier: ~10-30 req/min → initial_delay_ms=1500.
Sem autenticação (Pro API key opcional via COINGECKO_API_KEY env var).
Tier 2 — REST API.

Uso:
    adapter = CoinGeckoAdapter()
    async for dp in adapter.collect({"endpoint": "markets", "per_page": 250}):
        rows = engine.normalize(dp)
        await client.upsert_metrics_batch(rows)
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import datetime, timezone
from typing import AsyncIterator

import httpx
import structlog

from services.collector.adapters.base import BaseAdapter, RawDataPoint
from services.collector.adapters.rate_limited_mixin import RateLimitedMixin

log = structlog.get_logger(__name__)

_SOURCE_ID = "coingecko"
_SOURCE_TIER = 2
_SCHEMA_VERSION = "coingecko_v3"


class CoinGeckoAdapter(RateLimitedMixin, BaseAdapter):
    """
    Adapter REST para a CoinGecko API pública (v3).

    Endpoints suportados:
        markets      — /coins/markets   (top N tokens por market cap)
        coin         — /coins/{id}      (detalhe completo de um coin)
        market_chart — /coins/{id}/market_chart (histórico de preço)
        global       — /global          (métricas globais do mercado crypto)
    """

    BASE_URL = "https://api.coingecko.com/api/v3"

    ENDPOINTS = {
        "markets":      "/coins/markets",
        "coin":         "/coins/{id}",
        "market_chart": "/coins/{id}/market_chart",
        "global":       "/global",
    }

    def __init__(self) -> None:
        # Free tier: ~10-30 req/min
        self.__init_rate_limiter__(
            initial_delay_ms=1500.0,
            min_delay_ms=500.0,
            max_delay_ms=30_000.0,
            failure_threshold=5,
            timeout_seconds=90.0,
        )
        self._client: httpx.AsyncClient | None = None
        self._api_key: str | None = os.environ.get("COINGECKO_API_KEY")

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            headers = {"Accept": "application/json"}
            if self._api_key:
                headers["x-cg-pro-api-key"] = self._api_key
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                timeout=httpx.Timeout(30.0, connect=10.0),
                headers=headers,
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
            resp = await client.get("/ping", timeout=5.0)
            return resp.status_code == 200
        except Exception:
            return False

    async def validate_response(self, data: RawDataPoint) -> bool:
        payload = data.raw_payload
        endpoint = data.metadata.get("endpoint", "")
        if endpoint == "markets":
            return isinstance(payload, list) and len(payload) > 0
        if endpoint == "coin":
            return isinstance(payload, dict) and "id" in payload
        if endpoint == "market_chart":
            return isinstance(payload, dict) and "prices" in payload
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
            {"endpoint": "markets", "vs_currency": "usd", "per_page": 250, "page": 1}
            {"endpoint": "coin", "id": "uniswap"}
            {"endpoint": "market_chart", "id": "uniswap", "days": 1}
            {"endpoint": "global"}
        """
        endpoint = params.get("endpoint", "markets")

        if endpoint == "markets":
            async for dp in self.collect_markets(
                vs_currency=params.get("vs_currency", "usd"),
                per_page=params.get("per_page", 250),
                page=params.get("page", 1),
            ):
                yield dp
        elif endpoint == "coin":
            coin_id = params.get("id", "")
            if not coin_id:
                raise ValueError("collect(coin): 'id' obrigatório")
            async for dp in self.collect_coin(coin_id):
                yield dp
        elif endpoint == "market_chart":
            coin_id = params.get("id", "")
            if not coin_id:
                raise ValueError("collect(market_chart): 'id' obrigatório")
            async for dp in self.collect_market_chart(
                coin_id,
                days=params.get("days", 1),
            ):
                yield dp
        elif endpoint == "global":
            async for dp in self.collect_global():
                yield dp
        else:
            raise ValueError(f"CoinGeckoAdapter: endpoint desconhecido: {endpoint!r}")

    # ── Endpoint methods ───────────────────────────────────────────────────────

    async def collect_markets(
        self,
        vs_currency: str = "usd",
        per_page: int = 250,
        page: int = 1,
    ) -> AsyncIterator[RawDataPoint]:
        """GET /coins/markets — top tokens por market cap."""
        query = {
            "vs_currency": vs_currency,
            "order": "market_cap_desc",
            "per_page": str(per_page),
            "page": str(page),
            "sparkline": "false",
            "price_change_percentage": "1h,24h,7d,30d",
        }
        dp = await self._fetch_endpoint(
            path=self.ENDPOINTS["markets"],
            endpoint_key="markets",
            params=query,
        )
        if dp:
            yield dp

    async def collect_coin(self, coin_id: str) -> AsyncIterator[RawDataPoint]:
        """GET /coins/{id} — detalhe completo de um coin."""
        path = self.ENDPOINTS["coin"].format(id=coin_id)
        query = {
            "localization": "false",
            "tickers": "false",
            "market_data": "true",
            "community_data": "false",
            "developer_data": "false",
        }
        dp = await self._fetch_endpoint(
            path=path,
            endpoint_key="coin",
            params=query,
            extra_meta={"id": coin_id},
        )
        if dp:
            yield dp

    async def collect_market_chart(
        self,
        coin_id: str,
        days: int = 1,
    ) -> AsyncIterator[RawDataPoint]:
        """GET /coins/{id}/market_chart — histórico de preço."""
        path = self.ENDPOINTS["market_chart"].format(id=coin_id)
        query = {
            "vs_currency": "usd",
            "days": str(days),
            "interval": "hourly" if days <= 90 else "daily",
        }
        dp = await self._fetch_endpoint(
            path=path,
            endpoint_key="market_chart",
            params=query,
            extra_meta={"id": coin_id, "days": days},
        )
        if dp:
            yield dp

    async def collect_global(self) -> AsyncIterator[RawDataPoint]:
        """GET /global — métricas globais (total market cap, dominance, etc.)."""
        dp = await self._fetch_endpoint(
            path=self.ENDPOINTS["global"],
            endpoint_key="global",
        )
        if dp:
            yield dp

    # ── Internal ──────────────────────────────────────────────────────────────

    async def _fetch_endpoint(
        self,
        path: str,
        endpoint_key: str,
        params: dict | None = None,
        extra_meta: dict | None = None,
    ) -> RawDataPoint | None:
        url = f"{self.BASE_URL}{path}"
        log.debug("coingecko.fetch", endpoint=endpoint_key, url=url)

        await self._acquire()
        t0 = time.monotonic()

        try:
            response = await self._call_protected(self._do_get, path, params or {})
        except Exception as exc:
            log.error("coingecko.fetch_error", endpoint=endpoint_key, exc=str(exc))
            await self._report(503, (time.monotonic() - t0) * 1000)
            return None

        elapsed_ms = (time.monotonic() - t0) * 1000
        await self._report(response.status_code, elapsed_ms)

        if response.status_code == 429:
            log.warning("coingecko.rate_limited", endpoint=endpoint_key)
            return None

        if response.status_code != 200:
            log.warning(
                "coingecko.bad_status",
                endpoint=endpoint_key,
                status=response.status_code,
            )
            return None

        try:
            payload = response.json()
        except Exception as exc:
            log.error("coingecko.parse_error", endpoint=endpoint_key, exc=str(exc))
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

    async def _do_get(self, path: str, params: dict) -> httpx.Response:
        client = await self._get_client()
        return await client.get(path, params=params)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _sha256(payload: dict | list | str) -> str:
    if isinstance(payload, (dict, list)):
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    else:
        raw = str(payload)
    return hashlib.sha256(raw.encode()).hexdigest()
