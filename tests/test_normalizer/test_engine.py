# tests/test_normalizer/test_engine.py
"""Testes unitários para services/normalizer/engine.py (NormalizerEngine)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from services.normalizer.engine import NormalizerEngine


TS = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def engine() -> NormalizerEngine:
    return NormalizerEngine()


def _dp(make_raw_datapoint, source_id: str, payload, **metadata):
    return make_raw_datapoint(
        source_id=source_id,
        payload=payload,
        metadata=metadata,
    )


# ── dispatch por source_id ────────────────────────────────────────────────────

class TestDispatch:
    def test_defillama_protocols_dispatch(self, engine, make_raw_datapoint):
        dp = _dp(
            make_raw_datapoint,
            "defillama",
            [{"slug": "uniswap", "tvl": 1_000_000.0}],
            endpoint="protocols",
        )
        rows = engine.normalize(dp)
        assert len(rows) > 0
        assert all(r["source_id"] == "defillama" for r in rows)

    def test_defillama_fees_dispatch(self, engine, make_raw_datapoint):
        dp = _dp(
            make_raw_datapoint,
            "defillama",
            {"protocols": [{"slug": "uniswap", "total24h": 100_000.0}]},
            endpoint="fees",
        )
        rows = engine.normalize(dp)
        assert len(rows) > 0
        assert any(r["metric_name"] == "fees_24h_usd" for r in rows)

    def test_defillama_hacks_dispatch(self, engine, make_raw_datapoint):
        dp = _dp(
            make_raw_datapoint,
            "defillama",
            [{"defillamaId": "ronin", "amount": 625_000_000.0}],
            endpoint="hacks",
        )
        rows = engine.normalize(dp)
        assert len(rows) > 0
        assert all(r["metric_name"] == "hack_amount_usd" for r in rows)

    def test_defillama_unknown_endpoint_returns_empty(self, engine, make_raw_datapoint):
        dp = _dp(
            make_raw_datapoint,
            "defillama",
            {},
            endpoint="nonexistent",
        )
        assert engine.normalize(dp) == []

    def test_coingecko_markets_dispatch(self, engine, make_raw_datapoint):
        dp = _dp(
            make_raw_datapoint,
            "coingecko",
            [{"id": "bitcoin", "current_price": 50_000.0}],
            endpoint="markets",
        )
        rows = engine.normalize(dp)
        assert len(rows) > 0
        assert all(r["source_id"] == "coingecko" for r in rows)

    def test_coingecko_global_dispatch(self, engine, make_raw_datapoint):
        dp = _dp(
            make_raw_datapoint,
            "coingecko",
            {"data": {"total_market_cap": {"usd": 2_000_000_000_000.0}}},
            endpoint="global",
        )
        rows = engine.normalize(dp)
        assert len(rows) > 0
        assert any(r["metric_name"] == "total_market_cap_usd" for r in rows)

    def test_ethereum_rpc_block_dispatch(self, engine, make_raw_datapoint):
        block_result = {
            "number": "0x1",
            "timestamp": "0x65B3D280",
            "gasUsed": "0x5208",
            "gasLimit": "0x1C9C380",
            "transactions": [],
        }
        dp = _dp(
            make_raw_datapoint,
            "ethereum_rpc",
            {"result": block_result},
            endpoint="block",
        )
        rows = engine.normalize(dp)
        assert len(rows) > 0
        assert all(r["source_id"] == "ethereum_rpc" for r in rows)

    def test_ethereum_rpc_gas_price_dispatch(self, engine, make_raw_datapoint):
        dp = _dp(
            make_raw_datapoint,
            "ethereum_rpc",
            {"result": "0x5D21DBA00"},
            endpoint="gas_price",
        )
        rows = engine.normalize(dp)
        assert any(r["metric_name"] == "gas_price_gwei" for r in rows)

    def test_thegraph_generic_dispatch(self, engine, make_raw_datapoint):
        dp = _dp(
            make_raw_datapoint,
            "thegraph",
            {"data": {"someField": []}},
            endpoint="query",
            subgraph="my-subgraph",
        )
        # generic mapper may produce empty or non-empty — just no crash
        rows = engine.normalize(dp)
        assert isinstance(rows, list)

    def test_snapshot_proposals_dispatch(self, engine, make_raw_datapoint):
        dp = _dp(
            make_raw_datapoint,
            "snapshot",
            {"data": {"proposals": []}},
            endpoint="proposals",
        )
        rows = engine.normalize(dp)
        assert isinstance(rows, list)

    def test_unknown_source_returns_empty(self, engine, make_raw_datapoint):
        dp = _dp(
            make_raw_datapoint,
            "nonexistent_source",
            {"some": "data"},
        )
        rows = engine.normalize(dp)
        assert rows == []


# ── error handling ────────────────────────────────────────────────────────────

class TestErrorHandling:
    def test_bad_payload_type_returns_empty_not_raises(self, engine, make_raw_datapoint):
        dp = _dp(
            make_raw_datapoint,
            "defillama",
            "completely wrong type",  # expects list
            endpoint="protocols",
        )
        rows = engine.normalize(dp)
        assert rows == []

    def test_none_payload_returns_empty_not_raises(self, engine, make_raw_datapoint):
        dp = _dp(
            make_raw_datapoint,
            "coingecko",
            None,
            endpoint="markets",
        )
        rows = engine.normalize(dp)
        assert rows == []

    def test_normalize_never_raises(self, engine, make_raw_datapoint):
        for source in ["defillama", "coingecko", "ethereum_rpc", "thegraph", "snapshot"]:
            dp = _dp(make_raw_datapoint, source, object(), endpoint="bogus")
            # must not raise
            result = engine.normalize(dp)
            assert isinstance(result, list)


# ── row schema ────────────────────────────────────────────────────────────────

class TestRowSchema:
    REQUIRED_KEYS = {
        "timestamp", "protocol_id", "chain_id", "metric_name",
        "value_numeric", "value_json", "source_id", "confidence",
    }

    def test_defillama_row_has_all_keys(self, engine, make_raw_datapoint):
        dp = _dp(
            make_raw_datapoint,
            "defillama",
            [{"slug": "uniswap", "tvl": 1_000_000.0}],
            endpoint="protocols",
        )
        rows = engine.normalize(dp)
        assert rows
        for row in rows:
            assert self.REQUIRED_KEYS.issubset(row.keys()), (
                f"Row missing keys: {self.REQUIRED_KEYS - row.keys()}"
            )

    def test_coingecko_row_has_all_keys(self, engine, make_raw_datapoint):
        dp = _dp(
            make_raw_datapoint,
            "coingecko",
            [{"id": "bitcoin", "current_price": 50_000.0}],
            endpoint="markets",
        )
        rows = engine.normalize(dp)
        assert rows
        for row in rows:
            assert self.REQUIRED_KEYS.issubset(row.keys())

    def test_ethereum_row_has_all_keys(self, engine, make_raw_datapoint):
        dp = _dp(
            make_raw_datapoint,
            "ethereum_rpc",
            {"result": "0x5D21DBA00"},
            endpoint="gas_price",
        )
        rows = engine.normalize(dp)
        assert rows
        for row in rows:
            assert self.REQUIRED_KEYS.issubset(row.keys())
