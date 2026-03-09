# services/normalizer/mappers/ethereum_mapper.py

"""
Mappers puros para respostas da Ethereum JSON-RPC API.

Sem IO — recebem dicts e retornam listas de rows prontas para
TimescaleClient.upsert_metrics_batch().

Convenção de protocol_id:
    "_ethereum"        — métricas globais da rede (gas, fees)
    "block:{number}"   — métricas de um bloco específico

Schema de row retornado:
    {
        "timestamp":     datetime,
        "protocol_id":   str,
        "chain_id":      str | None,
        "metric_name":   str,
        "value_numeric": float | None,
        "value_json":    dict | None,
        "source_id":     str,
        "confidence":    float,
    }
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


_SOURCE = "ethereum_rpc"
_CONFIDENCE = 0.99   # Tier 1 — dado direto da chain
_CHAIN_ID = "ethereum"


# ── eth_getBlockByNumber ───────────────────────────────────────────────────────

def map_block(data: dict, collected_at: datetime) -> list[dict]:
    """
    Mapeia resultado de eth_getBlockByNumber para linhas protocol_metrics.

    Extrai: block_height, gas_used, gas_limit, tx_count, gas_utilization_pct,
            base_fee_gwei (EIP-1559), block_size_bytes.

    Usa timestamp do próprio bloco se disponível.
    """
    result = data.get("result")
    if not isinstance(result, dict):
        return []

    block_num_hex = result.get("number", "0x0")
    block_num = _hex_to_int(block_num_hex)

    # Timestamp do bloco (Unix seconds) → datetime
    block_ts_hex = result.get("timestamp")
    if block_ts_hex:
        ts = datetime.fromtimestamp(_hex_to_int(block_ts_hex), tz=timezone.utc)
    else:
        ts = collected_at

    gas_used = _hex_to_int(result.get("gasUsed", "0x0"))
    gas_limit = _hex_to_int(result.get("gasLimit", "0x1"))
    tx_list = result.get("transactions") or []
    tx_count = len(tx_list)
    size_bytes = _hex_to_int(result.get("size", "0x0"))

    gas_util_pct = (gas_used / gas_limit * 100.0) if gas_limit > 0 else None

    rows = _compact([
        _row(ts, "_ethereum", _CHAIN_ID, "block_height",       float(block_num)),
        _row(ts, "_ethereum", _CHAIN_ID, "gas_used",           float(gas_used)),
        _row(ts, "_ethereum", _CHAIN_ID, "gas_limit",          float(gas_limit)),
        _row(ts, "_ethereum", _CHAIN_ID, "tx_count",           float(tx_count)),
        _row(ts, "_ethereum", _CHAIN_ID, "gas_utilization_pct", gas_util_pct),
        _row(ts, "_ethereum", _CHAIN_ID, "block_size_bytes",   float(size_bytes) if size_bytes else None),
    ])

    # EIP-1559 base fee
    base_fee_hex = result.get("baseFeePerGas")
    if base_fee_hex:
        base_fee_gwei = _hex_to_int(base_fee_hex) / 1e9
        rows.append(_row(ts, "_ethereum", _CHAIN_ID, "base_fee_gwei", base_fee_gwei))

    return rows


# ── eth_blockNumber ────────────────────────────────────────────────────────────

def map_block_number(data: dict, collected_at: datetime) -> list[dict]:
    """
    Mapeia resultado de eth_blockNumber para uma linha protocol_metrics.

    Retorna: block_height como float (para TimescaleDB value_numeric).
    """
    result = data.get("result")
    if result is None:
        return []
    block_num = _hex_to_int(result)
    return [_row(collected_at, "_ethereum", _CHAIN_ID, "block_height", float(block_num))]


# ── eth_getBalance ─────────────────────────────────────────────────────────────

def map_balance(data: dict, address: str, collected_at: datetime) -> list[dict]:
    """
    Mapeia resultado de eth_getBalance para uma linha protocol_metrics.

    Converte wei → ETH.
    protocol_id = "wallet:{address_lower}"
    """
    result = data.get("result")
    if result is None:
        return []
    wei = _hex_to_int(result)
    eth = wei / 1e18
    protocol_id = f"wallet:{address.lower()}"
    return [_row(collected_at, protocol_id, _CHAIN_ID, "balance_eth", eth)]


# ── eth_feeHistory ─────────────────────────────────────────────────────────────

def map_fee_history(data: dict, collected_at: datetime) -> list[dict]:
    """
    Mapeia resultado de eth_feeHistory para linhas protocol_metrics.

    Gera:
        avg_base_fee_gwei  — média da janela
        max_base_fee_gwei  — máximo da janela
        avg_priority_fee_gwei (50th percentile)
    """
    result = data.get("result")
    if not isinstance(result, dict):
        return []

    base_fees_hex = result.get("baseFeePerGas") or []
    reward_matrix = result.get("reward") or []

    if not base_fees_hex:
        return []

    base_fees_gwei = [_hex_to_int(h) / 1e9 for h in base_fees_hex if h]

    rows = []
    if base_fees_gwei:
        avg_base = sum(base_fees_gwei) / len(base_fees_gwei)
        max_base = max(base_fees_gwei)
        rows.extend(_compact([
            _row(collected_at, "_ethereum", _CHAIN_ID, "avg_base_fee_gwei", avg_base),
            _row(collected_at, "_ethereum", _CHAIN_ID, "max_base_fee_gwei", max_base),
        ]))

    # 50th percentile priority fee (índice 1 da lista de percentis [25,50,75])
    if reward_matrix:
        p50_rewards = []
        for block_rewards in reward_matrix:
            if isinstance(block_rewards, list) and len(block_rewards) >= 2:
                p50_rewards.append(_hex_to_int(block_rewards[1]) / 1e9)
        if p50_rewards:
            avg_priority = sum(p50_rewards) / len(p50_rewards)
            rows.append(_row(
                collected_at, "_ethereum", _CHAIN_ID,
                "avg_priority_fee_p50_gwei", avg_priority
            ))

    return rows


# ── eth_gasPrice ───────────────────────────────────────────────────────────────

def map_gas_price(data: dict, collected_at: datetime) -> list[dict]:
    """Mapeia eth_gasPrice → gas_price_gwei."""
    result = data.get("result")
    if result is None:
        return []
    gwei = _hex_to_int(result) / 1e9
    return [_row(collected_at, "_ethereum", _CHAIN_ID, "gas_price_gwei", gwei)]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _row(
    ts: datetime,
    protocol_id: str,
    chain_id: str | None,
    metric_name: str,
    value_numeric: float | None,
    value_json: dict | None = None,
) -> dict:
    return {
        "timestamp":     ts,
        "protocol_id":   protocol_id,
        "chain_id":      chain_id,
        "metric_name":   metric_name,
        "value_numeric": value_numeric,
        "value_json":    value_json,
        "source_id":     _SOURCE,
        "confidence":    _CONFIDENCE,
    }


def _compact(rows: list[dict]) -> list[dict]:
    return [r for r in rows if r["value_numeric"] is not None]


def _hex_to_int(value: Any) -> int:
    """Converte hex string (0x...) ou int para int."""
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    try:
        return int(str(value), 16)
    except (ValueError, TypeError):
        return 0
