# services/collector/adapters/ethereum_rpc.py

"""
EthereumRPCAdapter — coleta dados on-chain via JSON-RPC (Tier 1).

Suporta qualquer node Ethereum compatível com JSON-RPC:
    Infura, Alchemy, QuickNode, node local.

ENV:
    ETHEREUM_RPC_URL   — endpoint JSON-RPC (default: http://localhost:8545)

Uso:
    adapter = EthereumRPCAdapter()
    async for dp in adapter.collect({"endpoint": "block"}):
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

_SOURCE_ID = "ethereum_rpc"
_SOURCE_TIER = 1
_SCHEMA_VERSION = "ethereum_jsonrpc_v1"
_REQUEST_ID = 1  # stateless adapter — ID fixo é suficiente


class EthereumRPCAdapter(RateLimitedMixin, BaseAdapter):
    """
    Adapter JSON-RPC para nodes Ethereum.

    Endpoints suportados via params["endpoint"]:
        block        — eth_getBlockByNumber (número ou "latest")
        block_number — eth_blockNumber (block height atual)
        balance      — eth_getBalance (saldo de um endereço)
        fee_history  — eth_feeHistory (histórico de gas/base fee)
        gas_price    — eth_gasPrice (gas price atual)
    """

    def __init__(self) -> None:
        # Nodes Ethereum toleram alto throughput — delay conservador
        self.__init_rate_limiter__(
            initial_delay_ms=100.0,
            min_delay_ms=50.0,
            max_delay_ms=5_000.0,
            failure_threshold=10,
            timeout_seconds=30.0,
        )
        self._rpc_url: str = os.environ.get(
            "ETHEREUM_RPC_URL", "http://localhost:8545"
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
            resp = await self._rpc_call("eth_blockNumber", [])
            return resp.status_code == 200
        except Exception:
            return False

    async def validate_response(self, data: RawDataPoint) -> bool:
        payload = data.raw_payload
        return (
            isinstance(payload, dict)
            and "result" in payload
            and payload.get("error") is None
        )

    def get_rate_limit_config(self) -> dict:
        return self.get_rate_limit_stats()

    def get_schema(self) -> dict:
        return {"source_id": _SOURCE_ID, "tier": _SOURCE_TIER}

    # ── collect() ─────────────────────────────────────────────────────────────

    async def collect(self, params: dict) -> AsyncIterator[RawDataPoint]:
        """
        Async generator de RawDataPoints.

        params["endpoint"] seleciona o método:
            {"endpoint": "block"}                                  → latest block
            {"endpoint": "block", "number": 19_000_000}           → bloco específico
            {"endpoint": "block_number"}                           → block height atual
            {"endpoint": "balance", "address": "0x..."}           → saldo ETH
            {"endpoint": "fee_history", "block_count": 10}        → histórico de fees
            {"endpoint": "gas_price"}                              → gas price atual
        """
        endpoint = params.get("endpoint", "block")

        if endpoint == "block":
            number = params.get("number", "latest")
            async for dp in self.collect_block(number):
                yield dp
        elif endpoint == "block_number":
            async for dp in self.collect_block_number():
                yield dp
        elif endpoint == "balance":
            address = params.get("address", "")
            if not address:
                raise ValueError("collect(balance): 'address' obrigatório")
            async for dp in self.collect_balance(address):
                yield dp
        elif endpoint == "fee_history":
            block_count = int(params.get("block_count", 10))
            async for dp in self.collect_fee_history(block_count):
                yield dp
        elif endpoint == "gas_price":
            async for dp in self.collect_gas_price():
                yield dp
        else:
            raise ValueError(f"EthereumRPCAdapter: endpoint desconhecido: {endpoint!r}")

    # ── Endpoint methods ───────────────────────────────────────────────────────

    async def collect_block(
        self, number: int | str = "latest"
    ) -> AsyncIterator[RawDataPoint]:
        """eth_getBlockByNumber — dados do bloco (sem txs completas)."""
        block_param = (
            number
            if isinstance(number, str)
            else hex(number)
        )
        dp = await self._fetch_rpc(
            method="eth_getBlockByNumber",
            params=[block_param, False],
            endpoint_key="block",
            extra_meta={"block_number": number},
        )
        if dp:
            yield dp

    async def collect_block_number(self) -> AsyncIterator[RawDataPoint]:
        """eth_blockNumber — block height atual."""
        dp = await self._fetch_rpc(
            method="eth_blockNumber",
            params=[],
            endpoint_key="block_number",
        )
        if dp:
            yield dp

    async def collect_balance(self, address: str) -> AsyncIterator[RawDataPoint]:
        """eth_getBalance — saldo de um endereço em wei."""
        dp = await self._fetch_rpc(
            method="eth_getBalance",
            params=[address, "latest"],
            endpoint_key="balance",
            extra_meta={"address": address},
        )
        if dp:
            yield dp

    async def collect_fee_history(
        self, block_count: int = 10
    ) -> AsyncIterator[RawDataPoint]:
        """eth_feeHistory — histórico de base fee e gas utilizado."""
        dp = await self._fetch_rpc(
            method="eth_feeHistory",
            params=[hex(block_count), "latest", [25, 50, 75]],
            endpoint_key="fee_history",
            extra_meta={"block_count": block_count},
        )
        if dp:
            yield dp

    async def collect_gas_price(self) -> AsyncIterator[RawDataPoint]:
        """eth_gasPrice — gas price atual (legacy, pré-EIP-1559)."""
        dp = await self._fetch_rpc(
            method="eth_gasPrice",
            params=[],
            endpoint_key="gas_price",
        )
        if dp:
            yield dp

    # ── Internal ──────────────────────────────────────────────────────────────

    async def _fetch_rpc(
        self,
        method: str,
        params: list,
        endpoint_key: str,
        extra_meta: dict | None = None,
    ) -> RawDataPoint | None:
        log.debug("ethereum_rpc.fetch", method=method, endpoint=endpoint_key)

        await self._acquire()
        t0 = time.monotonic()

        try:
            response = await self._call_protected(
                self._rpc_call, method, params
            )
        except Exception as exc:
            log.error("ethereum_rpc.fetch_error", method=method, exc=str(exc))
            await self._report(503, (time.monotonic() - t0) * 1000)
            return None

        elapsed_ms = (time.monotonic() - t0) * 1000
        await self._report(response.status_code, elapsed_ms)

        if response.status_code != 200:
            log.warning(
                "ethereum_rpc.bad_status",
                method=method,
                status=response.status_code,
            )
            return None

        try:
            payload = response.json()
        except Exception as exc:
            log.error("ethereum_rpc.parse_error", method=method, exc=str(exc))
            return None

        if payload.get("error"):
            log.warning(
                "ethereum_rpc.rpc_error",
                method=method,
                error=payload["error"],
            )
            return None

        now = datetime.now(tz=timezone.utc)
        meta: dict = {"endpoint": endpoint_key, "method": method}
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
            collection_method="json_rpc",
            url_or_endpoint=self._rpc_url,
            http_status=response.status_code,
            response_headers=dict(response.headers),
            metadata=meta,
        )

    async def _rpc_call(self, method: str, params: list) -> httpx.Response:
        client = await self._get_client()
        body = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": _REQUEST_ID,
        }
        return await client.post(self._rpc_url, json=body)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _sha256(payload: dict | list | str) -> str:
    if isinstance(payload, (dict, list)):
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    else:
        raw = str(payload)
    return hashlib.sha256(raw.encode()).hexdigest()
