# tests/test_adapters/test_base.py
"""Testes unitários para services/collector/adapters/base.py."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from services.collector.adapters.base import RawDataPoint


TS = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)


class TestRawDataPoint:
    def _make(self, **overrides) -> RawDataPoint:
        defaults = dict(
            source_id="defillama",
            source_tier=2,
            collection_timestamp=TS,
            data_timestamp=TS,
            raw_payload={"key": "value"},
            content_hash="abc123",
            schema_version="v1",
            collection_method="rest",
            url_or_endpoint="https://api.llama.fi/protocols",
            http_status=200,
            response_headers={"content-type": "application/json"},
            metadata={},
        )
        defaults.update(overrides)
        return RawDataPoint(**defaults)

    def test_construction(self):
        dp = self._make()
        assert dp.source_id == "defillama"
        assert dp.source_tier == 2
        assert dp.http_status == 200

    def test_fixture_from_conftest(self, make_raw_datapoint):
        dp = make_raw_datapoint("defillama", {"tvl": 1_000_000.0})
        assert dp.source_id == "defillama"
        assert dp.raw_payload == {"tvl": 1_000_000.0}
        assert dp.content_hash == "test-hash-abc123"

    def test_metadata_default_empty(self, make_raw_datapoint):
        dp = make_raw_datapoint("coingecko", [])
        assert dp.metadata == {}

    def test_metadata_passed_through(self, make_raw_datapoint):
        dp = make_raw_datapoint(
            "defillama",
            {},
            metadata={"endpoint": "protocols", "slug": "uniswap"},
        )
        assert dp.metadata["endpoint"] == "protocols"
        assert dp.metadata["slug"] == "uniswap"

    def test_payload_can_be_list(self, make_raw_datapoint):
        dp = make_raw_datapoint("defillama", [{"slug": "aave", "tvl": 1.0}])
        assert isinstance(dp.raw_payload, list)

    def test_payload_can_be_dict(self, make_raw_datapoint):
        dp = make_raw_datapoint("coingecko", {"data": {}})
        assert isinstance(dp.raw_payload, dict)

    def test_source_tier_from_factory(self, make_raw_datapoint):
        dp = make_raw_datapoint("ethereum_rpc", {}, source_tier=1)
        assert dp.source_tier == 1
