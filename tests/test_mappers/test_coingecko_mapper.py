# tests/test_mappers/test_coingecko_mapper.py
"""Testes unitários para services/normalizer/mappers/coingecko_mapper.py."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from services.normalizer.mappers import coingecko_mapper as cm


TS = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
_SOURCE = "coingecko"
_CONFIDENCE = 0.88


def _by_metric(rows: list[dict], name: str) -> list[dict]:
    return [r for r in rows if r["metric_name"] == name]


def _metric_names(rows: list[dict]) -> set[str]:
    return {r["metric_name"] for r in rows}


# ── map_coins_markets ─────────────────────────────────────────────────────────

class TestMapCoinsMarkets:
    def test_happy_path_full_coin(self):
        data = [
            {
                "id": "uniswap",
                "current_price": 10.0,
                "market_cap": 5_000_000_000.0,
                "total_volume": 200_000_000.0,
                "market_cap_rank": 15,
                "price_change_percentage_24h": -2.5,
                "circulating_supply": 500_000_000.0,
            }
        ]
        rows = cm.map_coins_markets(data, TS)
        names = _metric_names(rows)
        assert "price_usd" in names
        assert "market_cap_usd" in names
        assert "volume_24h_usd" in names
        assert "market_cap_rank" in names
        assert "price_change_24h_pct" in names
        assert "circulating_supply" in names

    def test_missing_fields_excluded(self):
        data = [{"id": "bitcoin", "current_price": 50_000.0}]
        rows = cm.map_coins_markets(data, TS)
        assert _by_metric(rows, "price_usd")
        assert not _by_metric(rows, "market_cap_usd")

    def test_no_id_skipped(self):
        data = [{"current_price": 100.0}]
        rows = cm.map_coins_markets(data, TS)
        assert rows == []

    def test_empty_list(self):
        assert cm.map_coins_markets([], TS) == []

    def test_source_and_confidence(self):
        data = [{"id": "bitcoin", "current_price": 50_000.0}]
        rows = cm.map_coins_markets(data, TS)
        for r in rows:
            assert r["source_id"] == _SOURCE
            assert r["confidence"] == pytest.approx(_CONFIDENCE)

    def test_multiple_coins(self):
        data = [
            {"id": "bitcoin", "current_price": 50_000.0},
            {"id": "ethereum", "current_price": 3_000.0},
        ]
        rows = cm.map_coins_markets(data, TS)
        ids = {r["protocol_id"] for r in rows}
        assert "bitcoin" in ids
        assert "ethereum" in ids

    def test_price_value(self):
        data = [{"id": "bitcoin", "current_price": 42_000.0}]
        rows = cm.map_coins_markets(data, TS)
        price_rows = _by_metric(rows, "price_usd")
        assert len(price_rows) == 1
        assert price_rows[0]["value_numeric"] == pytest.approx(42_000.0)

    def test_nan_price_excluded(self):
        data = [{"id": "bitcoin", "current_price": float("nan")}]
        rows = cm.map_coins_markets(data, TS)
        assert not _by_metric(rows, "price_usd")


# ── map_coin_detail ───────────────────────────────────────────────────────────

class TestMapCoinDetail:
    def _make_data(self, **market_data_kwargs) -> dict:
        return {"market_data": market_data_kwargs}

    def test_price_from_nested_usd(self):
        data = {"market_data": {"current_price": {"usd": 3_500.0, "eur": 3_100.0}}}
        rows = cm.map_coin_detail(data, "ethereum", TS)
        price_rows = _by_metric(rows, "price_usd")
        assert len(price_rows) == 1
        assert price_rows[0]["value_numeric"] == pytest.approx(3_500.0)

    def test_all_metrics_present(self):
        data = {
            "market_data": {
                "current_price": {"usd": 3_500.0},
                "market_cap": {"usd": 400_000_000_000.0},
                "fully_diluted_valuation": {"usd": 420_000_000_000.0},
                "total_volume": {"usd": 20_000_000_000.0},
                "price_change_percentage_24h": -1.5,
                "price_change_percentage_7d": 4.2,
                "price_change_percentage_30d": -8.1,
                "circulating_supply": 120_000_000.0,
                "total_supply": 120_000_000.0,
                "market_cap_rank": 2,
            }
        }
        rows = cm.map_coin_detail(data, "ethereum", TS)
        names = _metric_names(rows)
        assert {"price_usd", "market_cap_usd", "fdv_usd", "volume_24h_usd",
                "price_change_24h_pct", "price_change_7d_pct", "price_change_30d_pct",
                "circulating_supply", "total_supply", "market_cap_rank"}.issubset(names)

    def test_missing_market_data(self):
        rows = cm.map_coin_detail({}, "ethereum", TS)
        assert rows == []

    def test_coin_id_as_protocol_id(self):
        data = {"market_data": {"current_price": {"usd": 1.0}}}
        rows = cm.map_coin_detail(data, "my-coin", TS)
        assert all(r["protocol_id"] == "my-coin" for r in rows)


# ── map_market_chart ──────────────────────────────────────────────────────────

class TestMapMarketChart:
    def test_prices_parsed(self):
        ts_ms = 1705320000000  # 2024-01-15 12:00:00 UTC
        data = {"prices": [[ts_ms, 3_500.0]]}
        rows = cm.map_market_chart(data, "ethereum", TS)
        price_rows = _by_metric(rows, "price_usd")
        assert len(price_rows) == 1
        assert price_rows[0]["value_numeric"] == pytest.approx(3_500.0)

    def test_timestamp_from_data_not_collected_at(self):
        ts_ms = 1_700_000_000_000
        data = {"prices": [[ts_ms, 100.0]]}
        rows = cm.map_market_chart(data, "bitcoin", TS)
        expected_ts = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
        assert rows[0]["timestamp"] == expected_ts

    def test_all_series_mapped(self):
        ts_ms = 1705320000000
        data = {
            "prices": [[ts_ms, 3_500.0]],
            "market_caps": [[ts_ms, 400_000_000_000.0]],
            "total_volumes": [[ts_ms, 20_000_000_000.0]],
        }
        rows = cm.map_market_chart(data, "ethereum", TS)
        names = _metric_names(rows)
        assert {"price_usd", "market_cap_usd", "volume_24h_usd"}.issubset(names)

    def test_invalid_points_skipped(self):
        data = {"prices": [[1705320000000], "bad", None]}
        rows = cm.map_market_chart(data, "bitcoin", TS)
        assert rows == []

    def test_none_value_in_point_skipped(self):
        data = {"prices": [[1705320000000, None]]}
        rows = cm.map_market_chart(data, "bitcoin", TS)
        assert rows == []

    def test_empty_data(self):
        rows = cm.map_market_chart({}, "bitcoin", TS)
        assert rows == []


# ── map_global ────────────────────────────────────────────────────────────────

class TestMapGlobal:
    def test_total_market_cap(self):
        data = {"data": {"total_market_cap": {"usd": 2_500_000_000_000.0}}}
        rows = cm.map_global(data, TS)
        mcap_rows = _by_metric(rows, "total_market_cap_usd")
        assert len(mcap_rows) == 1
        assert mcap_rows[0]["value_numeric"] == pytest.approx(2_500_000_000_000.0)
        assert mcap_rows[0]["protocol_id"] == "_market"

    def test_total_volume(self):
        data = {"data": {"total_volume": {"usd": 100_000_000_000.0}}}
        rows = cm.map_global(data, TS)
        vol_rows = _by_metric(rows, "total_volume_24h_usd")
        assert len(vol_rows) == 1

    def test_dominance_metrics(self):
        data = {"data": {"market_cap_percentage": {"btc": 48.5, "eth": 17.2}}}
        rows = cm.map_global(data, TS)
        names = _metric_names(rows)
        assert "dominance_btc_pct" in names
        assert "dominance_eth_pct" in names

    def test_active_coins_and_markets(self):
        data = {"data": {"active_cryptocurrencies": 12000, "markets": 700}}
        rows = cm.map_global(data, TS)
        names = _metric_names(rows)
        assert "active_coins" in names
        assert "active_markets" in names

    def test_empty_data(self):
        rows = cm.map_global({}, TS)
        assert rows == []

    def test_missing_usd_in_total_mcap(self):
        data = {"data": {"total_market_cap": {"eur": 2_000_000_000_000.0}}}
        rows = cm.map_global(data, TS)
        assert not _by_metric(rows, "total_market_cap_usd")
