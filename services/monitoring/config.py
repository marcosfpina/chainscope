# services/monitoring/config.py

"""
MONITORING — Observabilidade completa do pipeline
"""

MONITORING_CONFIG = {

    "health_checks": {
        "sources": {
            "description": "Health de cada fonte de dados",
            "check_interval_seconds": 60,
            "metrics": [
                "is_reachable",
                "response_time_ms",
                "error_rate_pct",
                "last_successful_collection",
                "data_freshness_seconds",
                "rate_limit_remaining",
            ],
            "alerting": {
                "source_down": "source unreachable for > 5 min",
                "source_degraded": "error_rate > 10% over 15 min",
                "source_stale": "no new data for > 2x expected_interval",
            }
        },

        "pipeline": {
            "description": "Health de cada estágio do pipeline",
            "metrics": [
                "queue_depth",
                "processing_rate_per_second",
                "error_rate_per_second",
                "latency_p50_ms",
                "latency_p99_ms",
                "backpressure_level",
                "gpu_utilization_pct",
                "memory_usage_pct",
            ],
        },

        "storage": {
            "description": "Health dos databases",
            "metrics": [
                "disk_usage_pct",
                "query_latency_p99",
                "replication_lag_ms",
                "connection_pool_usage",
                "ingestion_rate",
            ],
        },

        "data_quality": {
            "description": "Qualidade dos dados coletados",
            "metrics": [
                "validation_pass_rate_pct",
                "cross_validation_conflict_rate_pct",
                "dedup_collision_rate_pct",
                "schema_compliance_pct",
                "freshness_sla_compliance_pct",
                "coverage_completeness_pct",
                "anomaly_detection_rate",
            ],
            "dashboards": [
                "data_quality_overview",
                "source_reliability_ranking",
                "coverage_gap_heatmap",
                "freshness_map",
            ]
        },
    },

    "logging": {
        "strategy": "structured_json",
        "levels": {
            "collector": "INFO",
            "validator": "WARNING",
            "normalizer": "INFO",
            "enricher": "INFO",
            "analyzer": "INFO",
            "api": "INFO",
        },
        "mandatory_fields": [
            "timestamp", "service", "trace_id",
            "source_id", "action", "duration_ms",
            "status", "error_type",
        ],
    },

    "tracing": {
        "description": "Distributed tracing para seguir um dado da coleta ao delivery",
        "implementation": "OpenTelemetry",
        "trace_structure": """
            Trace: collect_defillama_tvl
            ├── Span: http_request (duration, status)
            ├── Span: validate_response (passed, issues)
            ├── Span: normalize (transformations)
            ├── Span: store_timescaledb (rows_written)
            ├── Span: generate_embedding (model, latency)
            └── Span: update_graph (nodes_updated, edges_created)
        """
    },
}
