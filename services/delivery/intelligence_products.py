# services/delivery/intelligence_products.py

"""
INTELLIGENCE PRODUCTS — Outputs finais do pipeline
"""

INTELLIGENCE_PRODUCTS = {

    "daily_intelligence_brief": {
        "schedule": "daily at 06:00 UTC",
        "description": """
        Briefing diário automatizado gerado pelo LLM na B300.
        Sumariza os eventos mais relevantes das últimas 24h.
        """,
        "sections": [
            {
                "name": "market_overview",
                "content": "Resumo do mercado — preços, volumes, TVL total",
            },
            {
                "name": "notable_events",
                "content": "Top 10 eventos detectados pelo anomaly detection",
            },
            {
                "name": "governance_digest",
                "content": "Proposals importantes ativas/finalizadas",
            },
            {
                "name": "security_alerts",
                "content": "Novos incidents, audits, bounties",
            },
            {
                "name": "development_highlights",
                "content": "Releases, forks, novos repos significativos",
            },
            {
                "name": "research_spotlight",
                "content": "Papers/posts de pesquisa mais relevantes",
            },
            {
                "name": "regulatory_update",
                "content": "Movimentos regulatórios relevantes",
            },
            {
                "name": "risk_dashboard",
                "content": "Mudanças no risk landscape",
            },
        ],
        "generation_pipeline": """
            1. Aggregate all data from last 24h
            2. Run anomaly detection
            3. Rank events by impact score
            4. Generate structured summary via LLM
            5. Cross-reference with historical context
            6. Generate actionable insights
            7. Format + deliver
        """
    },

    "protocol_deep_dive": {
        "trigger": "on_demand or weekly_rotation",
        "description": """
        Análise profunda de um protocolo específico.
        Combina TODOS os dados disponíveis.
        """,
        "sections": [
            "executive_summary",
            "protocol_overview_and_history",
            "technology_deep_dive",
            "tokenomics_analysis",
            "on_chain_metrics_analysis",
            "competitive_landscape",
            "governance_analysis",
            "security_assessment",
            "developer_activity_assessment",
            "risk_factor_analysis",
            "scenario_modeling",
            "appendix_data_tables",
        ]
    },

    "ecosystem_map": {
        "schedule": "weekly",
        "description": """
        Mapa visual do ecossistema gerado a partir do knowledge graph.
        Mostra relações, dependências, fluxos.
        """,
        "views": [
            "full_ecosystem_topology",
            "defi_dependency_tree",
            "cross_chain_bridge_map",
            "developer_flow_sankey",
            "funding_network",
            "technology_stack_hierarchy",
        ]
    },

    "risk_radar": {
        "schedule": "continuous",
        "description": """
        Dashboard em tempo real de riscos sistêmicos.
        """,
        "risk_categories": [
            "smart_contract_risk",
            "oracle_dependency_risk",
            "bridge_risk",
            "centralization_risk",
            "liquidity_risk",
            "stablecoin_risk",
            "regulatory_risk",
            "mev_censorship_risk",
            "validator_concentration_risk",
        ]
    },

    "alpha_signals": {
        "schedule": "continuous",
        "description": """
        Sinais automatizados baseados em detecção de padrões.
        NÃO é trading advice — é intelligence para researchers.
        """,
        "signal_types": [
            "whale_accumulation_detected",
            "developer_surge_on_protocol",
            "governance_power_shift",
            "tvl_momentum_change",
            "new_protocol_rapid_growth",
            "security_concern_emerging",
            "regulatory_action_imminent",
            "technology_breakthrough_published",
            "cross_chain_migration_trend",
            "tokenomics_event_upcoming",    # unlock, emission change
        ]
    },
}
