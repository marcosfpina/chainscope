# services/normalizer/mappers/coingecko_mapper.py

"""
Mappers puros para respostas da CoinGecko API v3.

Sem IO — recebem dicts/lists e retornam listas de rows prontas para
TimescaleClient.upsert_metrics_batch().

Schema de row retornado:
    {
        "timestamp":     datetime,
        "protocol_id":   str,        # coin id (ex: "uniswap", "bitcoin")
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


_SOURCE = "coingecko"
_CONFIDENCE = 0.88   # Tier 2


# ── /coins/markets ────────────────────────────────────────────────────────────

def map_coins_markets(data: list[dict], collected_at: datetime) -> list[dict]:
    """
    Mapeia response de /coins/markets para linhas protocol_metrics.

    Cada coin gera até 9 linhas:
        price_usd, market_cap_usd, volume_24h_usd, market_cap_rank,
        price_change_1h_pct, price_change_24h_pct, price_change_7d_pct,
        price_change_30d_pct, circulating_supply
    """
    rows: list[dict] = []
    for item in data:
        coin_id = _coin_id(item)
        if not coin_id:
            continue

        rows.extend(_compact([
            _row(collected_at, coin_id, None, "price_usd",
                 _num(item.get("current_price"))),
            _row(collected_at, coin_id, None, "market_cap_usd",
                 _num(item.get("market_cap"))),
            _row(collected_at, coin_id, None, "volume_24h_usd",
                 _num(item.get("total_volume"))),
            _row(collected_at, coin_id, None, "market_cap_rank",
                 _num(item.get("market_cap_rank"))),
            _row(collected_at, coin_id, None, "price_change_1h_pct",
                 _num(item.get("price_change_percentage_1h_in_currency"))),
            _row(collected_at, coin_id, None, "price_change_24h_pct",
                 _num(item.get("price_change_percentage_24h"))),
            _row(collected_at, coin_id, None, "price_change_7d_pct",
                 _num(item.get("price_change_percentage_7d_in_currency"))),
            _row(collected_at, coin_id, None, "price_change_30d_pct",
                 _num(item.get("price_change_percentage_30d_in_currency"))),
            _row(collected_at, coin_id, None, "circulating_supply",
                 _num(item.get("circulating_supply"))),
        ]))

    return rows


# ── /coins/{id} ───────────────────────────────────────────────────────────────

def map_coin_detail(
    data: dict,
    coin_id: str,
    collected_at: datetime,
) -> list[dict]:
    """
    Mapeia response de /coins/{id} (market_data=true) para linhas protocol_metrics.

    Extrai métricas do sub-dict market_data em USD, mais tokenomics.
    """
    rows: list[dict] = []
    md = data.get("market_data") or {}

    def _usd(field: str) -> float | None:
        val = md.get(field)
        if isinstance(val, dict):
            return _num(val.get("usd"))
        return _num(val)

    rows.extend(_compact([
        _row(collected_at, coin_id, None, "price_usd",
             _usd("current_price")),
        _row(collected_at, coin_id, None, "market_cap_usd",
             _usd("market_cap")),
        _row(collected_at, coin_id, None, "fdv_usd",
             _usd("fully_diluted_valuation")),
        _row(collected_at, coin_id, None, "volume_24h_usd",
             _usd("total_volume")),
        _row(collected_at, coin_id, None, "price_change_24h_pct",
             _num(md.get("price_change_percentage_24h"))),
        _row(collected_at, coin_id, None, "price_change_7d_pct",
             _num(md.get("price_change_percentage_7d"))),
        _row(collected_at, coin_id, None, "price_change_30d_pct",
             _num(md.get("price_change_percentage_30d"))),
        _row(collected_at, coin_id, None, "circulating_supply",
             _num(md.get("circulating_supply"))),
        _row(collected_at, coin_id, None, "total_supply",
             _num(md.get("total_supply"))),
        _row(collected_at, coin_id, None, "market_cap_rank",
             _num(md.get("market_cap_rank"))),
    ]))

    return rows


# ── /coins/{id}/market_chart ─────────────────────────────────────────────────

def map_market_chart(
    data: dict,
    coin_id: str,
    collected_at: datetime,
) -> list[dict]:
    """
    Mapeia response de /coins/{id}/market_chart para linhas protocol_metrics.

    Cada ponto [timestamp_ms, value] → 1 row com timestamp real do dado.
    Gera rows para: price_usd, market_cap_usd, volume_24h_usd.
    """
    rows: list[dict] = []

    series = {
        "price_usd":        data.get("prices") or [],
        "market_cap_usd":   data.get("market_caps") or [],
        "volume_24h_usd":   data.get("total_volumes") or [],
    }

    for metric_name, points in series.items():
        for point in points:
            if not isinstance(point, (list, tuple)) or len(point) < 2:
                continue
            ts_ms, value = point[0], point[1]
            val = _num(value)
            if val is None:
                continue
            ts = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
            rows.append(_row(ts, coin_id, None, metric_name, val))

    return rows


# ── /global ───────────────────────────────────────────────────────────────────

def map_global(data: dict, collected_at: datetime) -> list[dict]:
    """
    Mapeia response de /global para linhas protocol_metrics.

    Usa protocol_id="_market" para métricas agregadas do mercado cripto.
    """
    rows: list[dict] = []
    gd = data.get("data") or {}

    # Total market cap em USD
    total_mcap = gd.get("total_market_cap") or {}
    rows.extend(_compact([
        _row(collected_at, "_market", None, "total_market_cap_usd",
             _num(total_mcap.get("usd"))),
    ]))

    # Total volume em USD
    total_vol = gd.get("total_volume") or {}
    rows.extend(_compact([
        _row(collected_at, "_market", None, "total_volume_24h_usd",
             _num(total_vol.get("usd"))),
    ]))

    # Dominância BTC e ETH
    dominance = gd.get("market_cap_percentage") or {}
    for symbol, pct in dominance.items():
        val = _num(pct)
        if val is not None:
            rows.append(_row(
                collected_at, "_market", None,
                f"dominance_{symbol.lower()}_pct", val
            ))

    # Número de coins ativos
    rows.extend(_compact([
        _row(collected_at, "_market", None, "active_coins",
             _num(gd.get("active_cryptocurrencies"))),
        _row(collected_at, "_market", None, "active_markets",
             _num(gd.get("markets"))),
    ]))

    return rows


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


def _num(val: Any) -> float | None:
    if val is None:
        return None
    try:
        f = float(val)
        return f if f == f else None   # NaN check
    except (TypeError, ValueError):
        return None


def _coin_id(item: dict) -> str:
    return (item.get("id") or "").strip().lower()
