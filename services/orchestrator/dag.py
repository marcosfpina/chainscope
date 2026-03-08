# services/orchestrator/dag.py

"""
ORCHESTRATOR — Gerencia o DAG de execução do pipeline
"""

PIPELINE_DAG = {
    "description": """
    Directed Acyclic Graph da execução.
    Cada node é uma tarefa, edges são dependências.
    """,

    "execution_engine": "custom_async",  # ou Prefect/Dagster/Temporal

    "dag_definition": {

        # ── Stage 1: Collection (paralelo por source) ──
        "collect": {
            "tasks": [
                {
                    "id": "collect_on_chain",
                    "parallel_workers": 32,
                    "sources": ["ethereum_rpc", "solana_rpc", "cosmos_lcd", "..."],
                    "priority": "CRITICAL",
                },
                {
                    "id": "collect_aggregators",
                    "parallel_workers": 16,
                    "sources": ["defillama", "coingecko", "l2beat", "..."],
                    "priority": "HIGH",
                },
                {
                    "id": "collect_governance",
                    "parallel_workers": 8,
                    "sources": ["snapshot", "tally", "forums", "..."],
                    "priority": "MEDIUM",
                },
                {
                    "id": "collect_github",
                    "parallel_workers": 8,
                    "sources": ["github_api"],
                    "priority": "MEDIUM",
                },
                {
                    "id": "collect_research",
                    "parallel_workers": 4,
                    "sources": ["arxiv", "blogs", "newsletters", "..."],
                    "priority": "LOW",
                },
                {
                    "id": "collect_social",
                    "parallel_workers": 8,
                    "sources": ["farcaster", "reddit", "..."],
                    "priority": "LOW",
                },
                {
                    "id": "collect_market",
                    "parallel_workers": 16,
                    "sources": ["ccxt", "coinalyze", "..."],
                    "priority": "CRITICAL",
                },
            ],
            "depends_on": [],
        },

        # ── Stage 2: Validate (após collection) ──
        "validate": {
            "tasks": [
                {
                    "id": "structural_validation",
                    "parallel_workers": 32,
                },
                {
                    "id": "cross_source_validation",
                    "parallel_workers": 16,
                    "requires": "multiple_sources_collected",
                },
            ],
            "depends_on": ["collect"],
        },

        # ── Stage 3: Normalize ──
        "normalize": {
            "tasks": [
                {
                    "id": "schema_normalization",
                    "parallel_workers": 32,
                },
                {
                    "id": "deduplication",
                    "parallel_workers": 8,
                },
            ],
            "depends_on": ["validate"],
        },

        # ── Stage 4: Store ──
        "store": {
            "tasks": [
                {"id": "store_timeseries", "target": "timescaledb"},
                {"id": "store_graph", "target": "neo4j"},
                {"id": "store_analytics", "target": "clickhouse"},
                {"id": "store_raw", "target": "object_storage"},
                {"id": "store_lineage", "target": "postgres"},
            ],
            "depends_on": ["normalize"],
        },

        # ── Stage 5: Enrich (usa a B300) ──
        "enrich": {
            "tasks": [
                {
                    "id": "generate_embeddings",
                    "target": "qdrant",
                    "gpu_required": True,
                },
                {
                    "id": "entity_extraction",
                    "gpu_required": True,
                },
                {
                    "id": "document_summarization",
                    "gpu_required": True,
                },
                {
                    "id": "risk_scoring",
                    "gpu_required": True,
                },
            ],
            "depends_on": ["store"],
        },

        # ── Stage 6: Analyze ──
        "analyze": {
            "tasks": [
                {"id": "anomaly_detection"},
                {"id": "correlation_engine"},
                {"id": "scorecard_generation"},
                {"id": "graph_analytics"},
            ],
            "depends_on": ["enrich"],
        },

        # ── Stage 7: Deliver ──
        "deliver": {
            "tasks": [
                {"id": "update_api_cache"},
                {"id": "generate_intelligence_products", "gpu_required": True},
                {"id": "send_alerts"},
                {"id": "export_reports"},
            ],
            "depends_on": ["analyze"],
        },
    },
}
