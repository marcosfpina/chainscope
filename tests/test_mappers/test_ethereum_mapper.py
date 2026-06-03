# tests/test_mappers/test_ethereum_mapper.py
"""Testes unitários para services/normalizer/mappers/ethereum_mapper.py."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from services.normalizer.mappers import ethereum_mapper as em


TS = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
_SOURCE = "ethereum_rpc"
_CONFIDENCE = 0.99
_CHAIN_ID = "ethereum"


def _by_metric(rows: list[dict], name: str) -> list[dict]:
    return [r for r in rows if r["metric_name"] == name]


def _metric_names(rows: list[dict]) -> set[str]:
    return {r["metric_name"] for r in rows}


# ── map_block ─────────────────────────────────────────────────────────────────

class TestMapBlock:
    def _make_block(self, **kwargs) -> dict:
        defaults = {
            "number": "0x11A0D9C",  # 18483612
            "timestamp": "0x6567C9E8",
            "gasUsed": "0xD82DB2",
            "gasLimit": "0x1C9C380",
            "transactions": ["0x" + "a" * 64] * 120,
            "size": "0x1F400",
        }
        defaults.update(kwargs)
        return {"result": defaults}

    def test_happy_path_metrics(self):
        data = self._make_block()
        rows = em.map_block(data, TS)
        names = _metric_names(rows)
        assert "block_height" in names
        assert "gas_used" in names
        assert "gas_limit" in names
        assert "tx_count" in names
        assert "gas_utilization_pct" in names
        assert "block_size_bytes" in names

    def test_tx_count_from_transactions_list(self):
        data = self._make_block(transactions=["0x1", "0x2", "0x3"])
        rows = em.map_block(data, TS)
        tx_rows = _by_metric(rows, "tx_count")
        assert tx_rows[0]["value_numeric"] == pytest.approx(3.0)

    def test_gas_utilization_pct(self):
        data = self._make_block(gasUsed="0x80000", gasLimit="0x100000")
        rows = em.map_block(data, TS)
        util_rows = _by_metric(rows, "gas_utilization_pct")
        assert util_rows[0]["value_numeric"] == pytest.approx(50.0)

    def test_eip1559_base_fee(self):
        # 50 gwei = 50 * 1e9 wei = 0xBA43B7400
        data = self._make_block(baseFeePerGas="0xBA43B7400")
        rows = em.map_block(data, TS)
        fee_rows = _by_metric(rows, "base_fee_gwei")
        assert len(fee_rows) == 1
        assert fee_rows[0]["value_numeric"] == pytest.approx(50.0)

    def test_no_base_fee_no_row(self):
        data = self._make_block()
        # no baseFeePerGas key
        rows = em.map_block(data, TS)
        assert not _by_metric(rows, "base_fee_gwei")

    def test_timestamp_from_block(self):
        # 0x65B3D280 = 1706201728 UNIX
        data = self._make_block(timestamp="0x65B3D280")
        rows = em.map_block(data, TS)
        expected = datetime.fromtimestamp(0x65B3D280, tz=timezone.utc)
        assert all(r["timestamp"] == expected for r in rows)

    def test_fallback_to_collected_at_when_no_timestamp(self):
        block = {
            "number": "0x1",
            "gasUsed": "0x5208",
            "gasLimit": "0x1C9C380",
            "transactions": [],
        }
        rows = em.map_block({"result": block}, TS)
        assert all(r["timestamp"] == TS for r in rows)

    def test_missing_result_returns_empty(self):
        assert em.map_block({}, TS) == []
        assert em.map_block({"result": None}, TS) == []
        assert em.map_block({"result": "bad"}, TS) == []

    def test_source_confidence_chain(self):
        data = self._make_block()
        rows = em.map_block(data, TS)
        for r in rows:
            assert r["source_id"] == _SOURCE
            assert r["confidence"] == pytest.approx(_CONFIDENCE)
            assert r["chain_id"] == _CHAIN_ID

    def test_protocol_id_is_ethereum(self):
        data = self._make_block()
        rows = em.map_block(data, TS)
        assert all(r["protocol_id"] == "_ethereum" for r in rows)


# ── map_block_number ──────────────────────────────────────────────────────────

class TestMapBlockNumber:
    def test_hex_to_block_height(self):
        data = {"result": "0x11A0D9C"}  # 18484636
        rows = em.map_block_number(data, TS)
        assert len(rows) == 1
        assert rows[0]["metric_name"] == "block_height"
        assert rows[0]["value_numeric"] == pytest.approx(18484636.0)

    def test_missing_result(self):
        assert em.map_block_number({}, TS) == []
        assert em.map_block_number({"result": None}, TS) == []

    def test_source_confidence(self):
        rows = em.map_block_number({"result": "0x1"}, TS)
        assert rows[0]["source_id"] == _SOURCE
        assert rows[0]["confidence"] == pytest.approx(_CONFIDENCE)

    def test_timestamp_propagated(self):
        rows = em.map_block_number({"result": "0xFF"}, TS)
        assert rows[0]["timestamp"] == TS


# ── map_balance ───────────────────────────────────────────────────────────────

class TestMapBalance:
    # 1 ETH = 1e18 wei = 0xDE0B6B3A7640000
    _ONE_ETH_HEX = "0xDE0B6B3A7640000"
    _ADDRESS = "0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B"

    def test_wei_to_eth_conversion(self):
        rows = em.map_balance({"result": self._ONE_ETH_HEX}, self._ADDRESS, TS)
        assert len(rows) == 1
        assert rows[0]["value_numeric"] == pytest.approx(1.0)
        assert rows[0]["metric_name"] == "balance_eth"

    def test_protocol_id_format(self):
        rows = em.map_balance({"result": "0x1"}, self._ADDRESS, TS)
        expected_id = f"wallet:{self._ADDRESS.lower()}"
        assert rows[0]["protocol_id"] == expected_id

    def test_address_lowercased(self):
        upper = "0xAB5801A7D398351B8BE11C439E05C5B3259AEC9B"
        rows = em.map_balance({"result": "0x1"}, upper, TS)
        assert rows[0]["protocol_id"] == f"wallet:{upper.lower()}"

    def test_missing_result(self):
        assert em.map_balance({}, self._ADDRESS, TS) == []
        assert em.map_balance({"result": None}, self._ADDRESS, TS) == []

    def test_chain_id(self):
        rows = em.map_balance({"result": "0x1"}, self._ADDRESS, TS)
        assert rows[0]["chain_id"] == _CHAIN_ID


# ── map_fee_history ───────────────────────────────────────────────────────────

class TestMapFeeHistory:
    def test_avg_and_max_base_fee(self):
        # 20 gwei and 30 gwei → avg=25, max=30
        gwei_20 = hex(20 * int(1e9))
        gwei_30 = hex(30 * int(1e9))
        data = {"result": {"baseFeePerGas": [gwei_20, gwei_30]}}
        rows = em.map_fee_history(data, TS)
        avg_rows = _by_metric(rows, "avg_base_fee_gwei")
        max_rows = _by_metric(rows, "max_base_fee_gwei")
        assert avg_rows[0]["value_numeric"] == pytest.approx(25.0)
        assert max_rows[0]["value_numeric"] == pytest.approx(30.0)

    def test_p50_priority_fee(self):
        # reward matrix with 3 percentiles [p25, p50, p75] — read index 1
        gwei_2 = hex(2 * int(1e9))
        gwei_3 = hex(3 * int(1e9))
        gwei_10 = hex(10 * int(1e9))
        data = {
            "result": {
                "baseFeePerGas": [hex(20 * int(1e9))],
                "reward": [
                    [gwei_2, gwei_3, gwei_10],
                    [gwei_2, gwei_3, gwei_10],
                ],
            }
        }
        rows = em.map_fee_history(data, TS)
        p50_rows = _by_metric(rows, "avg_priority_fee_p50_gwei")
        assert len(p50_rows) == 1
        assert p50_rows[0]["value_numeric"] == pytest.approx(3.0)

    def test_missing_result(self):
        assert em.map_fee_history({}, TS) == []
        assert em.map_fee_history({"result": None}, TS) == []

    def test_empty_base_fees(self):
        data = {"result": {"baseFeePerGas": []}}
        rows = em.map_fee_history(data, TS)
        assert rows == []


# ── map_gas_price ─────────────────────────────────────────────────────────────

class TestMapGasPrice:
    def test_hex_to_gwei(self):
        # 25 gwei = 25_000_000_000 wei = 0x5D21DBA00
        data = {"result": "0x5D21DBA00"}
        rows = em.map_gas_price(data, TS)
        assert len(rows) == 1
        assert rows[0]["metric_name"] == "gas_price_gwei"
        assert rows[0]["value_numeric"] == pytest.approx(25.0)

    def test_missing_result(self):
        assert em.map_gas_price({}, TS) == []
        assert em.map_gas_price({"result": None}, TS) == []

    def test_source_confidence(self):
        rows = em.map_gas_price({"result": "0x1"}, TS)
        assert rows[0]["source_id"] == _SOURCE
        assert rows[0]["confidence"] == pytest.approx(_CONFIDENCE)

    def test_protocol_id(self):
        rows = em.map_gas_price({"result": "0x1"}, TS)
        assert rows[0]["protocol_id"] == "_ethereum"


# ── _hex_to_int ───────────────────────────────────────────────────────────────

class TestHexToInt:
    def test_hex_string(self):
        assert em._hex_to_int("0xFF") == 255

    def test_integer_passthrough(self):
        assert em._hex_to_int(100) == 100

    def test_none_returns_zero(self):
        assert em._hex_to_int(None) == 0

    def test_invalid_string_returns_zero(self):
        assert em._hex_to_int("not-hex") == 0
