# services/normalizer/mappers/snapshot_mapper.py

"""
Mappers puros para respostas da Snapshot GraphQL API.

Sem IO — recebem dicts e retornam listas de rows prontas para
TimescaleClient.upsert_metrics_batch().

Convenção de protocol_id:
    "{space_id}"                — métricas do space (ex: "aave.eth")
    "{space_id}:proposal:{id}" — métricas de uma proposta específica

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


_SOURCE = "snapshot"
_CONFIDENCE = 0.90   # Tier 1.5 — off-chain governance


# ── Proposals ─────────────────────────────────────────────────────────────────

def map_proposals(
    data: dict,
    collected_at: datetime,
) -> list[dict]:
    """
    Mapeia response de query Proposals.

    Por space: proposal_count, active_proposal_count
    Por proposta: vote_count, scores_total, quorum, participation_pct,
                  time_remaining_hours (se state=active), quorum_reached (0/1)
    """
    rows: list[dict] = []
    proposals = (data.get("data") or {}).get("proposals") or []

    # Agrega por space
    space_counts: dict[str, dict] = {}
    for p in proposals:
        if not isinstance(p, dict):
            continue
        space = (p.get("space") or {}).get("id") or "unknown"
        if space not in space_counts:
            space_counts[space] = {"total": 0, "active": 0}
        space_counts[space]["total"] += 1
        if p.get("state") == "active":
            space_counts[space]["active"] += 1

    for space_id, counts in space_counts.items():
        rows.extend(_compact([
            _row(collected_at, space_id, None, "proposal_count",
                 float(counts["total"])),
            _row(collected_at, space_id, None, "active_proposal_count",
                 float(counts["active"])),
        ]))

    # Métricas por proposta
    now_ts = collected_at.timestamp()
    for p in proposals:
        if not isinstance(p, dict):
            continue
        space = (p.get("space") or {}).get("id") or "unknown"
        pid = p.get("id", "unknown")
        protocol_id = f"{space}:proposal:{pid[:12]}"

        votes = _num(p.get("votes"))
        scores_total = _num(p.get("scores_total"))
        quorum = _num(p.get("quorum"))
        end_ts = _num(p.get("end"))

        quorum_reached = None
        if scores_total is not None and quorum is not None and quorum > 0:
            quorum_reached = 1.0 if scores_total >= quorum else 0.0

        time_remaining = None
        if end_ts is not None and p.get("state") == "active":
            remaining = end_ts - now_ts
            time_remaining = max(0.0, remaining / 3600.0)  # → horas

        rows.extend(_compact([
            _row(collected_at, protocol_id, None, "vote_count", votes),
            _row(collected_at, protocol_id, None, "scores_total", scores_total),
            _row(collected_at, protocol_id, None, "quorum", quorum),
            _row(collected_at, protocol_id, None, "quorum_reached", quorum_reached),
            _row(collected_at, protocol_id, None, "time_remaining_hours", time_remaining),
        ]))

        # Score por opção de voto (choices[i] → scores[i])
        choices = p.get("choices") or []
        scores = p.get("scores") or []
        for i, (choice, score) in enumerate(zip(choices, scores)):
            val = _num(score)
            if val is not None and isinstance(choice, str):
                metric = f"score_{choice.lower().replace(' ', '_')[:20]}"
                rows.append(_row(collected_at, protocol_id, None, metric, val))

    return rows


# ── Votes ──────────────────────────────────────────────────────────────────────

def map_votes(
    data: dict,
    proposal_id: str,
    collected_at: datetime,
) -> list[dict]:
    """
    Mapeia response de query Votes para uma proposta.

    Por proposta: total_vp (voting power total), voter_count,
                  vp_top10_concentration (Herfindahl-like)
    """
    rows: list[dict] = []
    votes = (data.get("data") or {}).get("votes") or []

    if not votes:
        return []

    protocol_id = f"proposal:{proposal_id[:12]}"
    voter_count = len(votes)
    vp_values = [_num(v.get("vp")) or 0.0 for v in votes if isinstance(v, dict)]
    total_vp = sum(vp_values)

    # Concentração de voting power (top-10 como % do total)
    vp_concentration = None
    if total_vp > 0 and vp_values:
        top10 = sum(sorted(vp_values, reverse=True)[:10])
        vp_concentration = top10 / total_vp * 100.0

    rows.extend(_compact([
        _row(collected_at, protocol_id, None, "voter_count", float(voter_count)),
        _row(collected_at, protocol_id, None, "total_vp", total_vp),
        _row(collected_at, protocol_id, None, "vp_top10_concentration_pct", vp_concentration),
    ]))

    return rows


# ── Spaces ─────────────────────────────────────────────────────────────────────

def map_spaces(
    data: dict,
    collected_at: datetime,
) -> list[dict]:
    """
    Mapeia response de query Spaces.

    Por space: members, followers, proposals_count, votes_count,
               active_proposals, follower_growth (se disponível)
    """
    rows: list[dict] = []
    spaces = (data.get("data") or {}).get("spaces") or []

    for space in spaces:
        if not isinstance(space, dict):
            continue
        space_id = space.get("id", "unknown")

        rows.extend(_compact([
            _row(collected_at, space_id, None, "members",
                 _num(space.get("members"))),
            _row(collected_at, space_id, None, "followers",
                 _num(space.get("followers"))),
            _row(collected_at, space_id, None, "proposals_count",
                 _num(space.get("proposalsCount"))),
            _row(collected_at, space_id, None, "votes_count",
                 _num(space.get("votesCount"))),
            _row(collected_at, space_id, None, "active_proposals",
                 _num(space.get("activeProposals"))),
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
        return f if f == f else None  # NaN check
    except (TypeError, ValueError):
        return None
