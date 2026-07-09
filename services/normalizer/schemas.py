# services/normalizer/schemas.py

"""
NORMALIZED SCHEMAS — Tudo é normalizado para schemas padronizados
independente da fonte original
"""

# ── Protocol Entity (schema central) ──

PROTOCOL_SCHEMA = {
    "type": "object",
    "properties": {
        # Identificação
        "protocol_id": {"type": "string", "format": "slug"},
        "name": {"type": "string"},
        "symbol": {"type": "string"},
        "description": {"type": "string"},
        "logo_url": {"type": "string", "format": "uri"},

        # Classificação
        "category": {
            "type": "string",
            "enum": [
                "dex", "lending", "cdp", "bridge", "yield",
                "liquid_staking", "restaking", "derivatives",
                "options", "insurance", "launchpad", "nft_marketplace",
                "nft_lending", "rwa", "synthetics", "algo_stablecoin",
                "reserve_currency", "yield_aggregator", "cross_chain",
                "oracle", "privacy", "payments", "gaming",
                "social", "identity", "storage", "compute",
                "indexing", "infrastructure", "l1", "l2_rollup",
                "l2_optimistic", "l2_zk", "sidechain", "appchain",
                "da_layer", "interoperability", "mev", "wallet",
            ]
        },
        "sub_category": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}},

        # Chains
        "chains": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "chain_id": {"type": "string"},
                    "chain_name": {"type": "string"},
                    "contract_addresses": {
                        "type": "object",
                        "additionalProperties": {"type": "string"}
                    },
                    "deployment_date": {"type": "string", "format": "date"},
                    "tvl_usd": {"type": "number"},
                }
            }
        },

        # Métricas financeiras
        "metrics": {
            "type": "object",
            "properties": {
                "tvl_usd": {"type": "number"},
                "tvl_eth": {"type": "number"},
                "tvl_btc": {"type": "number"},
                "tvl_change_1d_pct": {"type": "number"},
                "tvl_change_7d_pct": {"type": "number"},
                "tvl_change_30d_pct": {"type": "number"},

                "volume_24h_usd": {"type": "number"},
                "volume_7d_usd": {"type": "number"},
                "volume_30d_usd": {"type": "number"},

                "fees_24h_usd": {"type": "number"},
                "fees_7d_usd": {"type": "number"},
                "fees_30d_usd": {"type": "number"},
                "fees_annualized_usd": {"type": "number"},

                "revenue_24h_usd": {"type": "number"},
                "revenue_30d_usd": {"type": "number"},
                "revenue_annualized_usd": {"type": "number"},

                "active_users_24h": {"type": "integer"},
                "active_users_7d": {"type": "integer"},
                "active_users_30d": {"type": "integer"},

                "transactions_24h": {"type": "integer"},
                "transactions_7d": {"type": "integer"},
            }
        },

        # Token economics
        "tokenomics": {
            "type": "object",
            "properties": {
                "token_address": {"type": "string"},
                "token_chain": {"type": "string"},
                "price_usd": {"type": "number"},
                "market_cap_usd": {"type": "number"},
                "fdv_usd": {"type": "number"},
                "circulating_supply": {"type": "number"},
                "total_supply": {"type": "number"},
                "max_supply": {"type": ["number", "null"]},
                "inflation_rate_annual_pct": {"type": "number"},
                "emission_schedule": {"type": "object"},
                "token_distribution": {
                    "type": "object",
                    "properties": {
                        "team": {"type": "number"},
                        "investors": {"type": "number"},
                        "community": {"type": "number"},
                        "treasury": {"type": "number"},
                        "ecosystem": {"type": "number"},
                    }
                },
                "vesting_schedule": {"type": "array"},
                "staking_apr_pct": {"type": "number"},
                "staking_ratio_pct": {"type": "number"},
            }
        },

        # Tecnologia
        "technology": {
            "type": "object",
            "properties": {
                "consensus_mechanism": {"type": "string"},
                "virtual_machine": {"type": "string"},
                "programming_languages": {"type": "array"},
                "proof_system": {"type": "string"},
                "data_availability": {"type": "string"},
                "finality_time_seconds": {"type": "number"},
                "tps_theoretical": {"type": "number"},
                "tps_actual": {"type": "number"},
                "block_time_seconds": {"type": "number"},
                "evm_compatible": {"type": "boolean"},
                "open_source": {"type": "boolean"},
                "upgrade_mechanism": {"type": "string"},
                "key_dependencies": {"type": "array"},
            }
        },

        # Governança
        "governance": {
            "type": "object",
            "properties": {
                "governance_type": {
                    "type": "string",
                    "enum": [
                        "token_voting", "conviction_voting",
                        "quadratic_voting", "multisig",
                        "optimistic_governance", "futarchy",
                        "council", "liquid_democracy", "none"
                    ]
                },
                "governance_framework": {"type": "string"},
                "snapshot_space": {"type": "string"},
                "tally_org": {"type": "string"},
                "forum_url": {"type": "string"},
                "proposal_count_total": {"type": "integer"},
                "proposal_count_active": {"type": "integer"},
                "voter_participation_pct": {"type": "number"},
                "top_delegates": {"type": "array"},
                "timelock_delay_hours": {"type": "number"},
                "quorum_requirement": {"type": "string"},
            }
        },

        # Segurança
        "security": {
            "type": "object",
            "properties": {
                "audits": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "auditor": {"type": "string"},
                            "date": {"type": "string"},
                            "scope": {"type": "string"},
                            "findings_critical": {"type": "integer"},
                            "findings_high": {"type": "integer"},
                            "findings_medium": {"type": "integer"},
                            "findings_low": {"type": "integer"},
                            "report_url": {"type": "string"},
                        }
                    }
                },
                "bug_bounty_program": {"type": "boolean"},
                "bug_bounty_max_usd": {"type": "number"},
                "bug_bounty_platform": {"type": "string"},
                "formal_verification": {"type": "boolean"},
                "incident_history": {"type": "array"},
                "admin_keys": {"type": "string"},
                "upgradeability": {"type": "string"},
                "multisig_config": {"type": "string"},
                "l2beat_stage": {"type": "string"},
                "l2beat_risk_summary": {"type": "object"},
            }
        },

        # Desenvolvimento
        "development": {
            "type": "object",
            "properties": {
                "github_org": {"type": "string"},
                "primary_repos": {"type": "array"},
                "total_repos": {"type": "integer"},
                "total_contributors": {"type": "integer"},
                "monthly_active_devs": {"type": "integer"},
                "weekly_commits": {"type": "integer"},
                "open_prs": {"type": "integer"},
                "open_issues": {"type": "integer"},
                "stars_total": {"type": "integer"},
                "last_commit_date": {"type": "string"},
                "code_languages": {"type": "object"},
                "documentation_quality_score": {"type": "number"},
            }
        },

        # Links
        "links": {
            "type": "object",
            "properties": {
                "website": {"type": "string"},
                "documentation": {"type": "string"},
                "whitepaper": {"type": "string"},
                "github": {"type": "string"},
                "twitter": {"type": "string"},
                "discord": {"type": "string"},
                "telegram": {"type": "string"},
                "forum": {"type": "string"},
                "blog": {"type": "string"},
                "explorer": {"type": "string"},
                "coingecko": {"type": "string"},
                "defillama": {"type": "string"},
            }
        },

        # Metadados de coleta
        "collection_metadata": {
            "type": "object",
            "properties": {
                "last_updated": {"type": "string", "format": "date-time"},
                "data_sources": {"type": "array"},
                "confidence_score": {"type": "number"},
                "completeness_score": {"type": "number"},
                "freshness_score": {"type": "number"},
            }
        },
    }
}
