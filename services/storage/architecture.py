# services/storage/architecture.py

"""
STORAGE ARCHITECTURE — Cada tipo de dado vai para o store ideal
"""

STORAGE_STRATEGY = {

    # ═══════════════════════════════════════════
    # TimescaleDB (PostgreSQL + time-series)
    # Para: Métricas numéricas com timestamp
    # ═══════════════════════════════════════════

    "timescaledb": {
        "use_for": [
            "price_ohlcv",
            "tvl_timeseries",
            "volume_timeseries",
            "fee_revenue_timeseries",
            "gas_prices",
            "funding_rates",
            "open_interest",
            "active_addresses",
            "transaction_counts",
            "validator_metrics",
            "mev_metrics",
            "stablecoin_supply",
            "l2_batch_costs",
        ],
        "schema_example": """
            -- Hypertable para métricas de protocolo
            CREATE TABLE protocol_metrics (
                timestamp       TIMESTAMPTZ NOT NULL,
                protocol_id     TEXT NOT NULL,
                chain_id        TEXT,
                metric_name     TEXT NOT NULL,
                value_numeric   DOUBLE PRECISION,
                value_json      JSONB,
                source_id       TEXT NOT NULL,
                confidence      REAL DEFAULT 1.0,
                PRIMARY KEY (timestamp, protocol_id, metric_name)
            );
            SELECT create_hypertable('protocol_metrics', 'timestamp',
                chunk_time_interval => INTERVAL '1 day');

            -- Continuous aggregates para queries rápidas
            CREATE MATERIALIZED VIEW protocol_metrics_hourly
            WITH (timescaledb.continuous) AS
            SELECT
                time_bucket('1 hour', timestamp) AS bucket,
                protocol_id,
                metric_name,
                AVG(value_numeric) as avg_value,
                MIN(value_numeric) as min_value,
                MAX(value_numeric) as max_value,
                LAST(value_numeric, timestamp) as last_value,
                COUNT(*) as sample_count
            FROM protocol_metrics
            GROUP BY bucket, protocol_id, metric_name;

            -- Retention policy
            SELECT add_retention_policy('protocol_metrics',
                INTERVAL '2 years');

            -- Compression policy (dados > 7 dias)
            ALTER TABLE protocol_metrics SET (
                timescaledb.compress,
                timescaledb.compress_segmentby = 'protocol_id, metric_name',
                timescaledb.compress_orderby = 'timestamp DESC'
            );
            SELECT add_compression_policy('protocol_metrics',
                INTERVAL '7 days');
        """,
        "retention": {
            "raw": "2 years",
            "hourly_aggregates": "5 years",
            "daily_aggregates": "forever",
        }
    },

    # ═══════════════════════════════════════════
    # Neo4j (Graph Database)
    # Para: Relações entre entidades
    # ═══════════════════════════════════════════

    "neo4j": {
        "use_for": [
            "protocol_relationships",
            "developer_contribution_graph",
            "token_dependency_graph",
            "wallet_entity_mapping",
            "technology_dependency_tree",
            "funding_network",
            "audit_coverage_map",
            "governance_delegate_network",
            "cross_chain_bridge_topology",
        ],
        "notes": "Schema definido na Fase 3.2"
    },

    # ═══════════════════════════════════════════
    # Qdrant (Vector Database)
    # Para: Embeddings e semantic search
    # ═══════════════════════════════════════════

    "qdrant": {
        "use_for": [
            "whitepaper_embeddings",
            "research_paper_embeddings",
            "documentation_embeddings",
            "audit_report_embeddings",
            "forum_post_embeddings",
            "governance_proposal_embeddings",
            "code_snippet_embeddings",
            "blog_post_embeddings",
        ],
        "collections": {
            "documents": {
                "vector_size": 1024,      # Depends on embedding model
                "distance": "cosine",
                "payload_schema": {
                    "doc_type": "keyword",
                    "protocol_id": "keyword",
                    "chain_id": "keyword",
                    "source_id": "keyword",
                    "language": "keyword",
                    "publish_date": "datetime",
                    "title": "text",
                    "chunk_index": "integer",
                    "total_chunks": "integer",
                    "parent_doc_id": "keyword",
                },
                "optimizers": {
                    "indexing_threshold": 20000,
                    "memmap_threshold": 50000,
                },
            },
            "code_snippets": {
                "vector_size": 768,
                "distance": "cosine",
                "payload_schema": {
                    "language": "keyword",
                    "repo": "keyword",
                    "file_path": "text",
                    "function_name": "keyword",
                    "protocol_id": "keyword",
                },
            },
        },
        "usage_patterns": [
            "Similar protocol discovery",
            "Related research retrieval",
            "Vulnerability pattern matching",
            "Technology comparison",
            "Natural language queries over corpus",
        ]
    },

    # ═══════════════════════════════════════════
    # ClickHouse (Analytics Engine)
    # Para: Queries analíticas massivas
    # ═══════════════════════════════════════════

    "clickhouse": {
        "use_for": [
            "historical_analytics_at_scale",
            "cross_protocol_comparisons",
            "market_microstructure_analysis",
            "on_chain_transaction_analytics",
            "aggregated_reporting",
        ],
        "schema_example": """
            CREATE TABLE on_chain_events (
                timestamp DateTime64(3),
                chain_id LowCardinality(String),
                block_number UInt64,
                tx_hash String,
                event_type LowCardinality(String),
                protocol_id LowCardinality(String),
                contract_address String,
                from_address String,
                to_address String,
                value_wei UInt256,
                value_usd Float64,
                gas_used UInt64,
                gas_price_gwei Float64,
                method_id String,
                log_data String,
                source_id LowCardinality(String)
            )
            ENGINE = MergeTree()
            PARTITION BY toYYYYMM(timestamp)
            ORDER BY (chain_id, protocol_id, timestamp)
            TTL timestamp + INTERVAL 3 YEAR;

            -- Materialized view for protocol daily stats
            CREATE MATERIALIZED VIEW protocol_daily_stats
            ENGINE = SummingMergeTree()
            PARTITION BY toYYYYMM(day)
            ORDER BY (protocol_id, chain_id, day)
            AS SELECT
                toDate(timestamp) as day,
                protocol_id,
                chain_id,
                count() as tx_count,
                uniqExact(from_address) as unique_users,
                sum(value_usd) as total_volume_usd,
                sum(gas_used * gas_price_gwei) / 1e9 as total_gas_eth
            FROM on_chain_events
            GROUP BY day, protocol_id, chain_id;
        """,
    },

    # ═══════════════════════════════════════════
    # Redis (Cache + State + Pub/Sub)
    # Para: State management, caching, messaging
    # ═══════════════════════════════════════════

    "redis": {
        "use_for": [
            "rate_limit_state",
            "collection_job_queue",
            "recent_data_cache",
            "deduplication_bloom_filter",
            "real_time_alerts_pubsub",
            "crawler_state_coordination",
            "api_response_cache",
        ],
        "key_patterns": {
            "rate_limit": "rl:{domain}:{endpoint}",
            "cache": "cache:{source}:{key}:{ttl}",
            "dedup": "dedup:bloom:{source}",
            "job": "job:queue:{priority}:{source}",
            "state": "state:collector:{collector_id}",
            "alert": "alert:channel:{severity}",
            "lock": "lock:distributed:{resource}",
        }
    },

    # ═══════════════════════════════════════════
    # Object Storage (MinIO / S3-compatible)
    # Para: Documentos raw, PDFs, snapshots
    # ═══════════════════════════════════════════

    "object_storage": {
        "use_for": [
            "raw_api_responses",
            "pdf_whitepapers",
            "audit_reports",
            "git_repo_snapshots",
            "large_dataset_exports",
            "backup_snapshots",
        ],
        "bucket_structure": {
            "raw-responses": "/{source}/{date}/{hash}.json.zst",
            "documents": "/{type}/{protocol}/{filename}",
            "snapshots": "/{date}/{database}/{table}.parquet",
            "exports": "/{report_type}/{date}/{format}/",
        },
        "compression": "zstandard",
        "retention": {
            "raw-responses": "90 days",
            "documents": "forever",
            "snapshots": "1 year",
        }
    },
}
