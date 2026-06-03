# tests/conftest.py
"""Fixtures compartilhadas entre todos os testes do CHAINSCOPE."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import httpx
import pytest

from services.collector.adapters.base import RawDataPoint


# ── Fixtures base ─────────────────────────────────────────────────────────────

@pytest.fixture
def collected_at() -> datetime:
    return datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def make_raw_datapoint(collected_at):
    """Factory de RawDataPoint para testes."""
    def _factory(
        source_id: str,
        payload,
        metadata: dict | None = None,
        source_tier: int = 2,
    ) -> RawDataPoint:
        return RawDataPoint(
            source_id=source_id,
            source_tier=source_tier,
            collection_timestamp=collected_at,
            data_timestamp=collected_at,
            raw_payload=payload,
            content_hash="test-hash-abc123",
            schema_version="test_v1",
            collection_method="test",
            url_or_endpoint="https://test.example.com",
            http_status=200,
            response_headers={},
            metadata=metadata or {},
        )
    return _factory


# ── HTTP mock helpers ─────────────────────────────────────────────────────────

def make_httpx_response(
    status_code: int = 200,
    json_data=None,
    headers: dict | None = None,
) -> MagicMock:
    """Cria um mock de httpx.Response."""
    mock = MagicMock(spec=httpx.Response)
    mock.status_code = status_code
    mock.json.return_value = json_data if json_data is not None else {}
    mock.headers = headers or {"content-type": "application/json"}
    return mock
