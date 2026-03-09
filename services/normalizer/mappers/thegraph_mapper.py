# services/normalizer/mappers/thegraph_mapper.py

"""
Mappers puros para respostas de subgraphs do The Graph.

Sem IO — recebem dicts e retornam listas de rows prontas para
TimescaleClient.upsert_metrics_batch().

Estratégia de mapeamento:
    Subgraphs têm schemas heterogêneos — o mapper genérico preserva os dados
    brutos em value_json para consulta posterior. Mappers específicos extraem
    métricas numéricas de subgraphs conhecidos (Uniswap v3, Aave, Compound).

Schema de row retornado:
    {
        "timestamp":     datetime,
        "protocol_id":   str,   # ex: "uniswap-v3:{pool_id}"
        "chain_id":      str | None,
        "metric_name":   str,
        "value_numeric": float | None,
        "value_json":    dict | None,
        "source_id":     str,
        "confidence":    float,
    }
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


_SOURCE = "thegraph"
_CONFIDENCE = 0.92   # Tier 1.5 — indexador, não direto da chain


# ── Mapper genérico ────────────────────────────────────────────────────────────

def map_generic(
    data: dict,
    subgraph_id: str,
    collected_at: datetime,
) -> list[dict]:
    """
    Mapper genérico para qualquer subgraph.

    Itera sobre as entidades retornadas em data["data"] e:
    - Para listas de entidades: gera uma row por entidade com value_json
    - Para valores numéricos no root: gera row com value_numeric

    Útil para subgraphs sem mapper dedicado.
    """
    rows: list[dict] = []
    graphql_data = data.get("data") or {}

    for entity_type, content in graphql_data.items():
        if isinstance(content, list):
            # Lista de entidades → uma row por entidade
            for entity in content:
                if not isinstance(entity, dict):
                    continue
                entity_id = str(entity.get("id", "unknown"))
                protocol_id = f"{subgraph_id}:{entity_id}"
                rows.append(_row(
                    collected_at, protocol_id, None,
                    f"entity_{entity_type}",
                    None,
                    value_json=entity,
                ))
                # Extrai métricas numéricas do primeiro nível da entidade
                rows.extend(_extract_numerics(
                    entity, protocol_id, entity_type, collected_at
                ))
        elif isinstance(content, dict):
            # Objeto único — ex: _meta, protocol
            entity_id = str(content.get("id", entity_type))
            protocol_id = f"{subgraph_id}:{entity_id}"
            rows.extend(_extract_numerics(content, protocol_id, entity_type, collected_at))

    return rows


# ── Uniswap v3 ────────────────────────────────────────────────────────────────

def map_uniswap_pools(
    data: dict,
    collected_at: datetime,
) -> list[dict]:
    """
    Mapper para subgraph uniswap/uniswap-v3, query pools.

    Campos extraídos por pool:
        tvl_usd, volume_24h_usd, fee_tier_bps, tx_count,
        liquidity, sqrt_price
    """
    rows: list[dict] = []
    pools = (data.get("data") or {}).get("pools") or []

    for pool in pools:
        if not isinstance(pool, dict):
            continue
        pool_id = pool.get("id", "unknown")
        protocol_id = f"uniswap-v3:{pool_id[:8]}"  # trunca para legibilidade

        rows.extend(_compact([
            _row(collected_at, protocol_id, None, "tvl_usd",
                 _num(pool.get("totalValueLockedUSD"))),
            _row(collected_at, protocol_id, None, "volume_24h_usd",
                 _num(pool.get("volumeUSD"))),
            _row(collected_at, protocol_id, None, "fee_tier_bps",
                 _num(pool.get("feeTier"))),
            _row(collected_at, protocol_id, None, "tx_count",
                 _num(pool.get("txCount"))),
        ]))

    return rows


# ── Aave v3 ───────────────────────────────────────────────────────────────────

def map_aave_reserves(
    data: dict,
    collected_at: datetime,
) -> list[dict]:
    """
    Mapper para subgraph aave/protocol-v3, query reserves.

    Campos extraídos por reserve:
        total_deposits_usd, total_borrows_usd,
        liquidity_rate (deposit APY), borrow_rate,
        utilization_rate
    """
    rows: list[dict] = []
    reserves = (data.get("data") or {}).get("reserves") or []

    for reserve in reserves:
        if not isinstance(reserve, dict):
            continue
        symbol = reserve.get("symbol", "unknown")
        protocol_id = f"aave-v3:{symbol.lower()}"

        total_liq = _num(reserve.get("totalLiquidity"))
        total_borrows = _num(reserve.get("totalCurrentVariableDebt"))
        util = None
        if total_liq and total_borrows and total_liq > 0:
            util = total_borrows / total_liq * 100.0

        rows.extend(_compact([
            _row(collected_at, protocol_id, None, "total_deposits_usd",
                 _num(reserve.get("totalLiquidityUSD"))),
            _row(collected_at, protocol_id, None, "total_borrows_usd",
                 _num(reserve.get("totalCurrentVariableDebtUSD"))),
            _row(collected_at, protocol_id, None, "liquidity_rate_pct",
                 _ray_to_pct(reserve.get("liquidityRate"))),
            _row(collected_at, protocol_id, None, "variable_borrow_rate_pct",
                 _ray_to_pct(reserve.get("variableBorrowRate"))),
            _row(collected_at, protocol_id, None, "utilization_rate_pct", util),
        ]))

    return rows


# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract_numerics(
    entity: dict,
    protocol_id: str,
    prefix: str,
    collected_at: datetime,
) -> list[dict]:
    """Extrai campos numéricos de um dict de entidade."""
    rows = []
    for key, value in entity.items():
        val = _num(value)
        if val is not None:
            rows.append(_row(
                collected_at, protocol_id, None,
                f"{prefix}_{key}", val
            ))
    return rows


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


def _num(val: Any) -> float | None:
    if val is None:
        return None
    try:
        f = float(val)
        return f if f == f else None  # NaN check
    except (TypeError, ValueError):
        return None


def _ray_to_pct(val: Any) -> float | None:
    """Converte Aave RAY (1e27) para percentual."""
    n = _num(val)
    if n is None:
        return None
    return n / 1e27 * 100.0
