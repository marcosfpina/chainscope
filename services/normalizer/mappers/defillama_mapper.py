# services/normalizer/mappers/defillama_mapper.py

"""
Mappers puros para respostas da DefiLlama API.

Sem IO — recebem dicts e retornam listas de rows prontas para
TimescaleClient.upsert_metrics_batch().

Schema de row retornado:
    {
        "timestamp":     datetime,
        "protocol_id":   str,
        "chain_id":      str | None,
        "metric_name":   str,        # nome canônico de schemas.py
        "value_numeric": float | None,
        "value_json":    dict | None,
        "source_id":     str,
        "confidence":    float,
    }
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


_SOURCE = "defillama"
_CONFIDENCE = 0.88   # Tier 2


# ── /v2/protocols ─────────────────────────────────────────────────────────────

def map_protocols_list(data: list[dict], collected_at: datetime) -> list[dict]:
    """
    Mapeia response de /v2/protocols para linhas protocol_metrics.

    Cada protocolo gera até 5 linhas:
        tvl_usd, tvl_change_1d_pct, tvl_change_7d_pct, tvl_change_1m_pct,
        mcap_tvl_ratio
    """
    rows: list[dict] = []
    for item in data:
        slug = _slug(item)
        if not slug:
            continue

        tvl = _num(item.get("tvl"))
        rows.extend(_compact([
            _row(collected_at, slug, None, "tvl_usd",           tvl),
            _row(collected_at, slug, None, "tvl_change_1d_pct", _num(item.get("change_1d"))),
            _row(collected_at, slug, None, "tvl_change_7d_pct", _num(item.get("change_7d"))),
            _row(collected_at, slug, None, "tvl_change_1m_pct", _num(item.get("change_1m"))),
        ]))

        # mcap/tvl ratio — só quando ambos existem e tvl > 0
        mcap = _num(item.get("mcap"))
        if mcap is not None and tvl and tvl > 0:
            rows.append(_row(collected_at, slug, None, "mcap_tvl_ratio", mcap / tvl))

    return rows


# ── /protocol/{slug} ──────────────────────────────────────────────────────────

def map_protocol_detail(
    data: dict,
    slug: str,
    collected_at: datetime,
) -> list[dict]:
    """
    Mapeia response de /protocol/{slug} para linhas protocol_metrics.

    Extrai:
        - tvl_usd_by_chain (por chain)
        - fees_24h_usd / revenue_24h_usd (se presentes)
        - token price_usd
    """
    rows: list[dict] = []

    # TVL por chain — currentChainTvls: {"Ethereum": 1234567.89, ...}
    chain_tvls: dict[str, Any] = data.get("currentChainTvls") or {}
    for chain_name, chain_tvl in chain_tvls.items():
        val = _num(chain_tvl)
        if val is not None:
            rows.append(_row(
                collected_at, slug,
                chain_name.lower(), "tvl_usd_by_chain", val
            ))

    # TVL total (raiz)
    tvl_total = _num(data.get("tvl"))
    if tvl_total is not None:
        rows.append(_row(collected_at, slug, None, "tvl_usd", tvl_total))

    # Token price
    price = _num(data.get("tokenPrice"))
    if price is not None:
        rows.append(_row(collected_at, slug, None, "price_usd", price))

    return rows


# ── /overview/fees ────────────────────────────────────────────────────────────

def map_fees_overview(data: dict, collected_at: datetime) -> list[dict]:
    """
    Mapeia response de /overview/fees para linhas protocol_metrics.

    Extrai fees_24h_usd e revenue_24h_usd por protocolo.
    """
    rows: list[dict] = []
    protocols: list[dict] = data.get("protocols") or []

    for item in protocols:
        slug = _slug(item)
        if not slug:
            continue

        rows.extend(_compact([
            _row(collected_at, slug, None, "fees_24h_usd",     _num(item.get("total24h"))),
            _row(collected_at, slug, None, "fees_7d_usd",      _num(item.get("total7d"))),
            _row(collected_at, slug, None, "fees_30d_usd",     _num(item.get("total30d"))),
            _row(collected_at, slug, None, "revenue_24h_usd",  _num(item.get("revenue24h"))),
            _row(collected_at, slug, None, "revenue_30d_usd",  _num(item.get("revenue30d"))),
        ]))

    return rows


# ── /hacks ────────────────────────────────────────────────────────────────────

def map_hacks(data: list[dict], collected_at: datetime) -> list[dict]:
    """
    Mapeia response de /hacks para linhas protocol_metrics.

    Usa value_json para preservar metadados do hack (data, técnica, etc.).
    """
    rows: list[dict] = []
    for item in data:
        slug = item.get("defillamaId") or _slugify(item.get("name", ""))
        if not slug:
            continue

        amount = _num(item.get("amount"))
        rows.append({
            "timestamp":     collected_at,
            "protocol_id":   slug,
            "chain_id":      None,
            "metric_name":   "hack_amount_usd",
            "value_numeric": amount,
            "value_json":    {
                "date":        item.get("date"),
                "technique":   item.get("technique"),
                "category":    item.get("category"),
                "chain":       item.get("chain"),
                "name":        item.get("name"),
            },
            "source_id":     _SOURCE,
            "confidence":    _CONFIDENCE,
        })

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
    """Remove linhas onde value_numeric é None."""
    return [r for r in rows if r["value_numeric"] is not None]


def _num(val: Any) -> float | None:
    """Converte para float, retorna None se inválido."""
    if val is None:
        return None
    try:
        f = float(val)
        return f if f == f else None   # NaN check
    except (TypeError, ValueError):
        return None


def _slug(item: dict) -> str:
    """Extrai o slug/id do protocolo do dict da DefiLlama."""
    return (item.get("slug") or item.get("id") or "").strip().lower()


def _slugify(name: str) -> str:
    """Transforma um nome em slug simples."""
    return name.lower().replace(" ", "-").replace("/", "-")
