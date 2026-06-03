# tests/test_mappers/test_defillama_mapper.py
"""Testes unitários para services/normalizer/mappers/defillama_mapper.py."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from services.normalizer.mappers import defillama_mapper as dm


TS = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
_SOURCE = "defillama"
_CONFIDENCE = 0.88


# ── helpers ───────────────────────────────────────────────────────────────────

def _metric_names(rows: list[dict]) -> set[str]:
    return {r["metric_name"] for r in rows}


def _by_metric(rows: list[dict], name: str) -> list[dict]:
    return [r for r in rows if r["metric_name"] == name]


# ── map_protocols_list ────────────────────────────────────────────────────────

class TestMapProtocolsList:
    def test_happy_path_full_protocol(self):
        data = [
            {
                "slug": "uniswap",
                "tvl": 5_000_000.0,
                "change_1d": 1.2,
                "change_7d": -3.4,
                "change_1m": 10.0,
                "mcap": 10_000_000.0,
            }
        ]
        rows = dm.map_protocols_list(data, TS)
        names = _metric_names(rows)
        assert "tvl_usd" in names
        assert "tvl_change_1d_pct" in names
        assert "tvl_change_7d_pct" in names
        assert "tvl_change_1m_pct" in names
        assert "mcap_tvl_ratio" in names

    def test_mcap_tvl_ratio_value(self):
        data = [{"slug": "aave", "tvl": 2_000_000.0, "mcap": 6_000_000.0}]
        rows = dm.map_protocols_list(data, TS)
        ratio_rows = _by_metric(rows, "mcap_tvl_ratio")
        assert len(ratio_rows) == 1
        assert ratio_rows[0]["value_numeric"] == pytest.approx(3.0)

    def test_mcap_tvl_ratio_skipped_when_tvl_zero(self):
        data = [{"slug": "aave", "tvl": 0.0, "mcap": 1_000_000.0}]
        rows = dm.map_protocols_list(data, TS)
        assert not _by_metric(rows, "mcap_tvl_ratio")

    def test_mcap_tvl_ratio_skipped_when_mcap_missing(self):
        data = [{"slug": "aave", "tvl": 1_000_000.0}]
        rows = dm.map_protocols_list(data, TS)
        assert not _by_metric(rows, "mcap_tvl_ratio")

    def test_missing_tvl_excluded(self):
        data = [{"slug": "compound", "change_1d": 0.5}]
        rows = dm.map_protocols_list(data, TS)
        assert not _by_metric(rows, "tvl_usd")

    def test_nan_tvl_excluded(self):
        data = [{"slug": "compound", "tvl": float("nan")}]
        rows = dm.map_protocols_list(data, TS)
        assert not _by_metric(rows, "tvl_usd")

    def test_string_tvl_excluded(self):
        data = [{"slug": "compound", "tvl": "not-a-number"}]
        rows = dm.map_protocols_list(data, TS)
        assert not _by_metric(rows, "tvl_usd")

    def test_item_without_slug_skipped(self):
        data = [{"tvl": 1_000_000.0}]
        rows = dm.map_protocols_list(data, TS)
        assert rows == []

    def test_empty_list(self):
        assert dm.map_protocols_list([], TS) == []

    def test_source_and_confidence(self):
        data = [{"slug": "uniswap", "tvl": 1.0}]
        rows = dm.map_protocols_list(data, TS)
        for r in rows:
            assert r["source_id"] == _SOURCE
            assert r["confidence"] == pytest.approx(_CONFIDENCE)

    def test_timestamp_propagated(self):
        data = [{"slug": "uniswap", "tvl": 1.0}]
        rows = dm.map_protocols_list(data, TS)
        assert all(r["timestamp"] == TS for r in rows)

    def test_multiple_protocols(self):
        data = [
            {"slug": "uniswap", "tvl": 1_000_000.0},
            {"slug": "aave", "tvl": 2_000_000.0},
        ]
        rows = dm.map_protocols_list(data, TS)
        protocol_ids = {r["protocol_id"] for r in rows}
        assert "uniswap" in protocol_ids
        assert "aave" in protocol_ids

    def test_uses_id_when_slug_absent(self):
        data = [{"id": "curve-dao-token", "tvl": 1.0}]
        rows = dm.map_protocols_list(data, TS)
        assert all(r["protocol_id"] == "curve-dao-token" for r in rows)


# ── map_protocol_detail ───────────────────────────────────────────────────────

class TestMapProtocolDetail:
    def test_tvl_by_chain(self):
        data = {
            "currentChainTvls": {
                "Ethereum": 1_000_000.0,
                "Polygon": 500_000.0,
            }
        }
        rows = dm.map_protocol_detail(data, "aave", TS)
        chain_rows = _by_metric(rows, "tvl_usd_by_chain")
        assert len(chain_rows) == 2
        chain_ids = {r["chain_id"] for r in chain_rows}
        assert "ethereum" in chain_ids
        assert "polygon" in chain_ids

    def test_tvl_total(self):
        data = {"tvl": 3_000_000.0}
        rows = dm.map_protocol_detail(data, "compound", TS)
        tvl_rows = _by_metric(rows, "tvl_usd")
        assert len(tvl_rows) == 1
        assert tvl_rows[0]["value_numeric"] == pytest.approx(3_000_000.0)

    def test_token_price(self):
        data = {"tokenPrice": 42.5}
        rows = dm.map_protocol_detail(data, "uniswap", TS)
        price_rows = _by_metric(rows, "price_usd")
        assert len(price_rows) == 1
        assert price_rows[0]["value_numeric"] == pytest.approx(42.5)

    def test_none_chain_tvl_skipped(self):
        data = {"currentChainTvls": {"Ethereum": None}}
        rows = dm.map_protocol_detail(data, "aave", TS)
        assert not _by_metric(rows, "tvl_usd_by_chain")

    def test_empty_data(self):
        rows = dm.map_protocol_detail({}, "aave", TS)
        assert rows == []

    def test_protocol_id_preserved(self):
        data = {"tvl": 1.0}
        rows = dm.map_protocol_detail(data, "my-protocol", TS)
        assert all(r["protocol_id"] == "my-protocol" for r in rows)


# ── map_fees_overview ────────────────────────────────────────────────────────

class TestMapFeesOverview:
    def test_happy_path(self):
        data = {
            "protocols": [
                {
                    "slug": "uniswap",
                    "total24h": 100_000.0,
                    "total7d": 700_000.0,
                    "total30d": 3_000_000.0,
                    "revenue24h": 10_000.0,
                    "revenue30d": 300_000.0,
                }
            ]
        }
        rows = dm.map_fees_overview(data, TS)
        names = _metric_names(rows)
        assert "fees_24h_usd" in names
        assert "fees_7d_usd" in names
        assert "fees_30d_usd" in names
        assert "revenue_24h_usd" in names
        assert "revenue_30d_usd" in names

    def test_missing_fee_fields_excluded(self):
        data = {"protocols": [{"slug": "uniswap"}]}
        rows = dm.map_fees_overview(data, TS)
        assert rows == []

    def test_no_protocols_key(self):
        rows = dm.map_fees_overview({}, TS)
        assert rows == []

    def test_protocol_without_slug_skipped(self):
        data = {"protocols": [{"total24h": 1000.0}]}
        rows = dm.map_fees_overview(data, TS)
        assert rows == []

    def test_multiple_protocols(self):
        data = {
            "protocols": [
                {"slug": "aave", "total24h": 50_000.0},
                {"slug": "compound", "total24h": 30_000.0},
            ]
        }
        rows = dm.map_fees_overview(data, TS)
        ids = {r["protocol_id"] for r in rows}
        assert "aave" in ids
        assert "compound" in ids


# ── map_hacks ─────────────────────────────────────────────────────────────────

class TestMapHacks:
    def test_happy_path(self):
        data = [
            {
                "defillamaId": "ronin",
                "amount": 625_000_000.0,
                "date": 1648152000,
                "technique": "Compromised private keys",
                "category": "Bridge",
                "chain": "Ethereum",
                "name": "Ronin Bridge",
            }
        ]
        rows = dm.map_hacks(data, TS)
        assert len(rows) == 1
        r = rows[0]
        assert r["protocol_id"] == "ronin"
        assert r["metric_name"] == "hack_amount_usd"
        assert r["value_numeric"] == pytest.approx(625_000_000.0)
        assert r["value_json"]["technique"] == "Compromised private keys"
        assert r["value_json"]["chain"] == "Ethereum"

    def test_missing_defillamaId_falls_back_to_name(self):
        data = [{"name": "Harvest Finance", "amount": 34_000_000.0}]
        rows = dm.map_hacks(data, TS)
        assert len(rows) == 1
        assert rows[0]["protocol_id"] == "harvest-finance"

    def test_missing_amount_still_produces_row(self):
        data = [{"defillamaId": "some-hack"}]
        rows = dm.map_hacks(data, TS)
        assert len(rows) == 1
        assert rows[0]["value_numeric"] is None

    def test_no_id_and_no_name_skipped(self):
        data = [{"amount": 1000.0}]
        rows = dm.map_hacks(data, TS)
        assert rows == []

    def test_empty_list(self):
        assert dm.map_hacks([], TS) == []

    def test_source_confidence(self):
        data = [{"defillamaId": "hack", "amount": 1.0}]
        rows = dm.map_hacks(data, TS)
        assert rows[0]["source_id"] == _SOURCE
        assert rows[0]["confidence"] == pytest.approx(_CONFIDENCE)
