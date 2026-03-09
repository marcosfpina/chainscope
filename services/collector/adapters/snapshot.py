# services/collector/adapters/snapshot.py

"""
SnapshotAdapter — coleta governance data via GraphQL (Tier 1.5).

Snapshot Hub: https://hub.snapshot.org/graphql
Sem autenticação necessária no free tier.

Spaces monitorados por default:
    aave.eth, uniswap, compound-governance.eth, balancer.eth,
    gitcoindao.eth, opcollective.eth, arbitrumfoundation.eth,
    safe.eth, lido-snapshot.eth, curve.eth

Uso:
    adapter = SnapshotAdapter()
    async for dp in adapter.collect({
        "endpoint": "proposals",
        "spaces": ["aave.eth", "uniswap"],
        "state": "active",
    }):
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

_SOURCE_ID = "snapshot"
_SOURCE_TIER = 1
_SCHEMA_VERSION = "snapshot_v1"
_HUB_URL = "https://hub.snapshot.org/graphql"

# Governance spaces relevantes para DeFi
DEFAULT_SPACES = [
    "aave.eth",
    "uniswap",
    "compound-governance.eth",
    "balancer.eth",
    "gitcoindao.eth",
    "opcollective.eth",
    "arbitrumfoundation.eth",
    "safe.eth",
    "lido-snapshot.eth",
    "curve.eth",
]

# ── Queries GraphQL ────────────────────────────────────────────────────────────

_QUERY_PROPOSALS = """
query Proposals($spaces: [String!], $state: String, $first: Int, $skip: Int) {
  proposals(
    first: $first
    skip: $skip
    where: { space_in: $spaces, state: $state }
    orderBy: "created"
    orderDirection: desc
  ) {
    id
    title
    state
    space { id name }
    author
    created
    start
    end
    votes
    quorum
    scores
    scores_total
    scores_state
    choices
    type
  }
}
"""

_QUERY_VOTES = """
query Votes($proposal: String!, $first: Int, $skip: Int) {
  votes(
    first: $first
    skip: $skip
    where: { proposal: $proposal }
    orderBy: "vp"
    orderDirection: desc
  ) {
    id
    voter
    choice
    vp
    vp_by_strategy
    reason
    created
  }
}
"""

_QUERY_SPACES = """
query Spaces($ids: [String!], $first: Int, $skip: Int) {
  spaces(
    first: $first
    skip: $skip
    where: { id_in: $ids }
  ) {
    id
    name
    about
    network
    symbol
    members
    followers
    proposalsCount
    votesCount
    activeProposals
  }
}
"""


class SnapshotAdapter(RateLimitedMixin, BaseAdapter):
    """
    Adapter GraphQL para Snapshot governance.

    Endpoints via params["endpoint"]:
        proposals — lista propostas por space(s)
        votes     — votos de uma proposta específica
        spaces    — metadados de governance spaces
    """

    def __init__(self) -> None:
        # Sem API key — delay conservador para evitar throttling
        self.__init_rate_limiter__(
            initial_delay_ms=500.0,
            min_delay_ms=200.0,
            max_delay_ms=15_000.0,
            failure_threshold=5,
            timeout_seconds=60.0,
        )
        self._client: httpx.AsyncClient | None = None

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0, connect=10.0),
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
            resp = await self._gql_post(
                query="{ spaces(first: 1) { id } }",
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
            endpoint    — "proposals" | "votes" | "spaces"
            spaces      — list[str], spaces a consultar (default: DEFAULT_SPACES)
            state       — "active" | "closed" | "pending" | "" (default: "")
            proposal    — str, ID da proposta (obrigatório para endpoint="votes")
            ids         — list[str] de space IDs (para endpoint="spaces")
            first       — paginação: itens por página (default: 100)
            skip        — paginação: offset (default: 0)
        """
        endpoint = params.get("endpoint", "proposals")

        if endpoint == "proposals":
            spaces = params.get("spaces") or DEFAULT_SPACES
            state = params.get("state", "")
            first = int(params.get("first", 100))
            skip = int(params.get("skip", 0))
            async for dp in self.collect_proposals(
                spaces=spaces, state=state, first=first, skip=skip
            ):
                yield dp

        elif endpoint == "votes":
            proposal_id = params.get("proposal", "")
            if not proposal_id:
                raise ValueError("collect(votes): 'proposal' ID obrigatório")
            first = int(params.get("first", 1000))
            skip = int(params.get("skip", 0))
            async for dp in self.collect_votes(
                proposal_id=proposal_id, first=first, skip=skip
            ):
                yield dp

        elif endpoint == "spaces":
            ids = params.get("ids") or DEFAULT_SPACES
            first = int(params.get("first", 50))
            skip = int(params.get("skip", 0))
            async for dp in self.collect_spaces(
                ids=ids, first=first, skip=skip
            ):
                yield dp

        else:
            raise ValueError(f"SnapshotAdapter: endpoint desconhecido: {endpoint!r}")

    # ── Endpoint methods ───────────────────────────────────────────────────────

    async def collect_proposals(
        self,
        spaces: list[str] | None = None,
        state: str = "",
        first: int = 100,
        skip: int = 0,
    ) -> AsyncIterator[RawDataPoint]:
        """Lista propostas de governance dos spaces monitorados."""
        variables: dict = {
            "spaces": spaces or DEFAULT_SPACES,
            "first": first,
            "skip": skip,
        }
        if state:
            variables["state"] = state

        dp = await self._fetch_snapshot(
            query=_QUERY_PROPOSALS,
            variables=variables,
            endpoint_key="proposals",
            extra_meta={"spaces": (spaces or DEFAULT_SPACES)[:5], "state": state},
        )
        if dp:
            yield dp

    async def collect_votes(
        self,
        proposal_id: str,
        first: int = 1000,
        skip: int = 0,
    ) -> AsyncIterator[RawDataPoint]:
        """Votos de uma proposta específica."""
        variables = {
            "proposal": proposal_id,
            "first": first,
            "skip": skip,
        }
        dp = await self._fetch_snapshot(
            query=_QUERY_VOTES,
            variables=variables,
            endpoint_key="votes",
            extra_meta={"proposal": proposal_id},
        )
        if dp:
            yield dp

    async def collect_spaces(
        self,
        ids: list[str] | None = None,
        first: int = 50,
        skip: int = 0,
    ) -> AsyncIterator[RawDataPoint]:
        """Metadados dos governance spaces."""
        variables = {
            "ids": ids or DEFAULT_SPACES,
            "first": first,
            "skip": skip,
        }
        dp = await self._fetch_snapshot(
            query=_QUERY_SPACES,
            variables=variables,
            endpoint_key="spaces",
            extra_meta={"ids": (ids or DEFAULT_SPACES)[:5]},
        )
        if dp:
            yield dp

    # ── Internal ──────────────────────────────────────────────────────────────

    async def _fetch_snapshot(
        self,
        query: str,
        variables: dict,
        endpoint_key: str,
        extra_meta: dict | None = None,
    ) -> RawDataPoint | None:
        log.debug("snapshot.fetch", endpoint=endpoint_key)

        await self._acquire()
        t0 = time.monotonic()

        try:
            response = await self._call_protected(
                self._gql_post, query, variables
            )
        except Exception as exc:
            log.error("snapshot.fetch_error", endpoint=endpoint_key, exc=str(exc))
            await self._report(503, (time.monotonic() - t0) * 1000)
            return None

        elapsed_ms = (time.monotonic() - t0) * 1000
        await self._report(response.status_code, elapsed_ms)

        if response.status_code == 429:
            log.warning("snapshot.rate_limited", endpoint=endpoint_key)
            return None

        if response.status_code != 200:
            log.warning(
                "snapshot.bad_status",
                endpoint=endpoint_key,
                status=response.status_code,
            )
            return None

        try:
            payload = response.json()
        except Exception as exc:
            log.error("snapshot.parse_error", endpoint=endpoint_key, exc=str(exc))
            return None

        if payload.get("errors"):
            log.warning(
                "snapshot.graphql_errors",
                endpoint=endpoint_key,
                errors=payload["errors"][:2],
            )

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
            url_or_endpoint=_HUB_URL,
            http_status=response.status_code,
            response_headers=dict(response.headers),
            metadata=meta,
        )

    async def _gql_post(
        self,
        query: str,
        variables: dict,
    ) -> httpx.Response:
        client = await self._get_client()
        body = {"query": query, "variables": variables}
        return await client.post(_HUB_URL, json=body)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _sha256(payload: dict | list | str) -> str:
    if isinstance(payload, (dict, list)):
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    else:
        raw = str(payload)
    return hashlib.sha256(raw.encode()).hexdigest()
