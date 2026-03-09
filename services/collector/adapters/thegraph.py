# services/collector/adapters/thegraph.py

"""
TheGraphAdapter — coleta subgraph data via GraphQL (Tier 1.5).

Suporta The Graph Hosted Service e Subgraph Studio.

ENV:
    THEGRAPH_API_KEY   — API key para Subgraph Studio (opcional no free tier)

Uso:
    adapter = TheGraphAdapter()
    async for dp in adapter.collect({
        "endpoint": "query",
        "subgraph": "uniswap/uniswap-v3",
        "query": "{ pools(first: 10) { id feeTier } }",
    }):
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

_SOURCE_ID = "thegraph"
_SOURCE_TIER = 1
_SCHEMA_VERSION = "thegraph_v1"

# Hosted service — subgraph name (ex: "uniswap/uniswap-v3")
_HOSTED_URL = "https://api.thegraph.com/subgraphs/name/{subgraph}"
# Subgraph Studio — subgraph ID (ex: "abc123...")
_STUDIO_URL = "https://gateway.thegraph.com/api/{api_key}/subgraphs/id/{subgraph_id}"


class TheGraphAdapter(RateLimitedMixin, BaseAdapter):
    """
    Adapter GraphQL para The Graph (hosted service + Subgraph Studio).

    params["endpoint"] suportados:
        query       — executa uma query GraphQL arbitrária num subgraph
        introspect  — introspection do schema do subgraph

    Subgraphs conhecidos (params["subgraph"]):
        uniswap/uniswap-v3
        aave/protocol-v3
        compound-finance/compound-v2
        balancer-labs/balancer-v2
        curvefi/curve-finance

    Para Subgraph Studio usar params["subgraph_id"] em vez de params["subgraph"].
    """

    def __init__(self) -> None:
        self.__init_rate_limiter__(
            initial_delay_ms=200.0,
            min_delay_ms=100.0,
            max_delay_ms=10_000.0,
            failure_threshold=5,
            timeout_seconds=60.0,
        )
        self._api_key: str | None = os.environ.get("THEGRAPH_API_KEY")
        self._client: httpx.AsyncClient | None = None

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(60.0, connect=10.0),
                headers={"Content-Type": "application/json"},
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
            # Introspection simples num subgraph público
            resp = await self._graphql_post(
                url=_HOSTED_URL.format(subgraph="uniswap/uniswap-v3"),
                query="{ _meta { block { number } } }",
                variables={},
            )
            return resp.status_code == 200
        except Exception:
            return False

    async def validate_response(self, data: RawDataPoint) -> bool:
        payload = data.raw_payload
        return (
            isinstance(payload, dict)
            and "data" in payload
            and payload.get("errors") is None
        )

    def get_rate_limit_config(self) -> dict:
        return self.get_rate_limit_stats()

    def get_schema(self) -> dict:
        return {"source_id": _SOURCE_ID, "tier": _SOURCE_TIER}

    # ── collect() ─────────────────────────────────────────────────────────────

    async def collect(self, params: dict) -> AsyncIterator[RawDataPoint]:
        """
        Async generator de RawDataPoints.

        params:
            endpoint    — "query" | "introspect"
            subgraph    — nome no hosted service (ex: "uniswap/uniswap-v3")
            subgraph_id — ID no Subgraph Studio (ex: "abc123...")
            query       — string GraphQL (obrigatório para endpoint="query")
            variables   — dict de variáveis GraphQL (opcional)
            first       — paginação: número de entidades (default: 100)
            skip        — paginação: offset (default: 0)
        """
        endpoint = params.get("endpoint", "query")

        if endpoint == "query":
            query = params.get("query", "")
            if not query:
                raise ValueError("collect(query): 'query' GraphQL obrigatório")
            subgraph = params.get("subgraph", "")
            subgraph_id = params.get("subgraph_id", "")
            if not subgraph and not subgraph_id:
                raise ValueError(
                    "collect(query): 'subgraph' ou 'subgraph_id' obrigatório"
                )
            variables = params.get("variables") or {}
            variables.setdefault("first", params.get("first", 100))
            variables.setdefault("skip", params.get("skip", 0))
            async for dp in self.collect_query(
                query=query,
                subgraph=subgraph,
                subgraph_id=subgraph_id,
                variables=variables,
            ):
                yield dp

        elif endpoint == "introspect":
            subgraph = params.get("subgraph", "")
            subgraph_id = params.get("subgraph_id", "")
            if not subgraph and not subgraph_id:
                raise ValueError(
                    "collect(introspect): 'subgraph' ou 'subgraph_id' obrigatório"
                )
            async for dp in self.collect_introspect(subgraph, subgraph_id):
                yield dp

        else:
            raise ValueError(f"TheGraphAdapter: endpoint desconhecido: {endpoint!r}")

    # ── Endpoint methods ───────────────────────────────────────────────────────

    async def collect_query(
        self,
        query: str,
        subgraph: str = "",
        subgraph_id: str = "",
        variables: dict | None = None,
    ) -> AsyncIterator[RawDataPoint]:
        """Executa query GraphQL num subgraph."""
        url = self._build_url(subgraph, subgraph_id)
        dp = await self._fetch_graphql(
            url=url,
            query=query,
            variables=variables or {},
            endpoint_key="query",
            extra_meta={
                "subgraph": subgraph or subgraph_id,
                "query_preview": query[:100],
            },
        )
        if dp:
            yield dp

    async def collect_introspect(
        self,
        subgraph: str = "",
        subgraph_id: str = "",
    ) -> AsyncIterator[RawDataPoint]:
        """Schema introspection do subgraph."""
        url = self._build_url(subgraph, subgraph_id)
        introspect_query = """
        {
          __schema {
            types {
              name
              kind
              fields { name type { name kind ofType { name kind } } }
            }
          }
        }
        """
        dp = await self._fetch_graphql(
            url=url,
            query=introspect_query,
            variables={},
            endpoint_key="introspect",
            extra_meta={"subgraph": subgraph or subgraph_id},
        )
        if dp:
            yield dp

    # ── Internal ──────────────────────────────────────────────────────────────

    def _build_url(self, subgraph: str, subgraph_id: str) -> str:
        if subgraph_id and self._api_key:
            return _STUDIO_URL.format(
                api_key=self._api_key,
                subgraph_id=subgraph_id,
            )
        if subgraph:
            return _HOSTED_URL.format(subgraph=subgraph)
        raise ValueError("TheGraphAdapter: subgraph ou subgraph_id obrigatório")

    async def _fetch_graphql(
        self,
        url: str,
        query: str,
        variables: dict,
        endpoint_key: str,
        extra_meta: dict | None = None,
    ) -> RawDataPoint | None:
        log.debug("thegraph.fetch", endpoint=endpoint_key, url=url)

        await self._acquire()
        t0 = time.monotonic()

        try:
            response = await self._call_protected(
                self._graphql_post, url, query, variables
            )
        except Exception as exc:
            log.error("thegraph.fetch_error", endpoint=endpoint_key, exc=str(exc))
            await self._report(503, (time.monotonic() - t0) * 1000)
            return None

        elapsed_ms = (time.monotonic() - t0) * 1000
        await self._report(response.status_code, elapsed_ms)

        if response.status_code == 429:
            log.warning("thegraph.rate_limited", endpoint=endpoint_key)
            return None

        if response.status_code != 200:
            log.warning(
                "thegraph.bad_status",
                endpoint=endpoint_key,
                status=response.status_code,
            )
            return None

        try:
            payload = response.json()
        except Exception as exc:
            log.error("thegraph.parse_error", endpoint=endpoint_key, exc=str(exc))
            return None

        if payload.get("errors"):
            log.warning(
                "thegraph.graphql_errors",
                endpoint=endpoint_key,
                errors=payload["errors"][:2],
            )
            # Retorna mesmo com erros parciais — data pode ser parcialmente válida

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
            content_hash=_sha256(payload),
            schema_version=_SCHEMA_VERSION,
            collection_method="graphql",
            url_or_endpoint=url,
            http_status=response.status_code,
            response_headers=dict(response.headers),
            metadata=meta,
        )

    async def _graphql_post(
        self,
        url: str,
        query: str,
        variables: dict,
    ) -> httpx.Response:
        client = await self._get_client()
        body = {"query": query, "variables": variables}
        return await client.post(url, json=body)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _sha256(payload: dict | list | str) -> str:
    if isinstance(payload, (dict, list)):
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    else:
        raw = str(payload)
    return hashlib.sha256(raw.encode()).hexdigest()
