# services/collector/engine.py

"""
COLLECTOR ENGINE — Arquitetura de alto nível
O Claude Code vai implementar isto
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import asyncio


class CollectionMethod(Enum):
    REST_API = "rest_api"
    GRAPHQL = "graphql"
    WEBSOCKET = "websocket"
    JSON_RPC = "json_rpc"
    RSS_ATOM = "rss_atom"
    HTML_PARSE = "html_parse"
    DISCOURSE_API = "discourse_api"
    GITHUB_API = "github_api"
    GRPC = "grpc"
    SSE = "server_sent_events"
    PDF_EXTRACTION = "pdf_extraction"
    GIT_CLONE = "git_clone"


class Priority(Enum):
    CRITICAL = 1      # On-chain data, prices
    HIGH = 2          # Protocol metrics, TVL
    MEDIUM = 3        # Governance, dev activity
    LOW = 4           # Social, research papers
    BACKGROUND = 5    # Historical backfill


@dataclass
class CollectionTask:
    source_id: str
    method: CollectionMethod
    priority: Priority
    schedule: str                    # cron expression
    parameters: dict[str, Any]
    rate_limit: dict[str, int]
    retry_policy: dict[str, Any]
    validation_rules: list[str]
    enrichment_pipeline: list[str]
    output_schema: str
    freshness_requirement_seconds: int
    dependencies: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


# ── Collection Schedule Map ──
COLLECTION_SCHEDULES = {
    # Real-time (WebSocket/SSE streams)
    "realtime": {
        "interval": "continuous",
        "sources": [
            "ethereum_rpc.new_blocks",
            "ethereum_rpc.pending_txs",
            "ethereum_beacon.head_events",
            "exchange_websockets.trades",
            "exchange_websockets.orderbook",
            "mempool_monitoring",
        ]
    },

    # Every 1 minute
    "1min": {
        "cron": "* * * * *",
        "sources": [
            "exchange_tickers",
            "funding_rates",
            "gas_prices",
        ]
    },

    # Every 5 minutes
    "5min": {
        "cron": "*/5 * * * *",
        "sources": [
            "defillama_tvl_current",
            "dex_volumes_current",
            "bridge_flows",
            "l2_batch_submissions",
        ]
    },

    # Every 15 minutes
    "15min": {
        "cron": "*/15 * * * *",
        "sources": [
            "coingecko_prices",
            "open_interest_aggregated",
            "mev_relay_data",
        ]
    },

    # Hourly
    "hourly": {
        "cron": "0 * * * *",
        "sources": [
            "defillama_full_refresh",
            "token_terminal_metrics",
            "l2beat_tvl",
            "validator_set_changes",
            "governance_new_proposals",
        ]
    },

    # Every 6 hours
    "6h": {
        "cron": "0 */6 * * *",
        "sources": [
            "github_commit_activity",
            "npm_download_stats",
            "forum_new_posts",
            "snapshot_proposals",
            "audit_new_reports",
        ]
    },

    # Daily
    "daily": {
        "cron": "0 2 * * *",  # 2 AM UTC
        "sources": [
            "github_deep_scan",
            "dune_daily_queries",
            "flipside_daily_queries",
            "research_papers_new",
            "regulatory_updates",
            "newsletter_digest",
            "rekt_news_check",
            "immunefi_bounties",
            "electric_capital_repos",
        ]
    },

    # Weekly
    "weekly": {
        "cron": "0 3 * * 1",  # Monday 3 AM UTC
        "sources": [
            "full_protocol_rescan",
            "whitepaper_updates",
            "documentation_changes",
            "l2beat_risk_assessment",
            "code4rena_new_contests",
            "developer_report_generation",
        ]
    },

    # Monthly
    "monthly": {
        "cron": "0 4 1 * *",  # 1st of month
        "sources": [
            "full_taxonomy_refresh",
            "historical_backfill_gaps",
            "source_health_audit",
            "data_quality_report",
        ]
    },
}
