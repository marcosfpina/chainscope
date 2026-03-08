# services/analysis/query_library.py

"""
QUERY LIBRARY — Análises pré-programadas que rodam em schedule
Cada query produz um "intelligence product" consumível
"""

ANALYTICAL_QUERIES = {

    # ═══════════════════════════════════════════
    # PROTOCOL INTELLIGENCE
    # ═══════════════════════════════════════════

    "protocol_health_scorecard": {
        "description": """
        Scorecard holístico para cada protocolo monitorado.
        Combina múltiplas dimensões em um score composto.
        """,
        "schedule": "daily",
        "dimensions": {
            "financial_health": {
                "weight": 0.25,
                "metrics": [
                    "tvl_trend_30d",           # Growing, stable, declining
                    "revenue_vs_emissions",     # Protocol earning more than emitting?
                    "fee_consistency",           # Coefficient of variation
                    "treasury_runway_months",    # Treasury / monthly burn
                    "tvl_concentration",         # HHI across chains/pools
                ]
            },
            "technical_health": {
                "weight": 0.25,
                "metrics": [
                    "commit_frequency_trend",
                    "contributor_diversity",      # Bus factor
                    "dependency_freshness",       # Are deps up to date?
                    "test_coverage_proxy",        # CI pass rate, test files ratio
                    "doc_quality_score",
                    "time_since_last_upgrade",
                ]
            },
            "security_health": {
                "weight": 0.25,
                "metrics": [
                    "audit_recency_months",
                    "audit_coverage_pct",         # % of codebase audited
                    "bug_bounty_exists",
                    "bug_bounty_amount_vs_tvl",
                    "incident_history_severity",
                    "admin_key_risk",             # Multisig? Timelock? EOA?
                    "upgradeability_risk",
                ]
            },
            "community_health": {
                "weight": 0.15,
                "metrics": [
                    "governance_participation_trend",
                    "unique_voters_growth",
                    "forum_activity_trend",
                    "developer_community_growth",
                    "user_retention_proxy",        # Returning addresses
                ]
            },
            "market_health": {
                "weight": 0.10,
                "metrics": [
                    "liquidity_depth",
                    "volume_to_mcap_ratio",
                    "token_holder_distribution",   # Gini coefficient
                    "insider_selling_pressure",    # Vesting unlocks
                    "correlation_to_eth_btc",
                ]
            },
        },
        "output": "protocol_scorecard_v1",
    },

    "tvl_flow_analysis": {
        "description": """
        Rastreia movimentação de TVL entre protocolos e chains.
        Identifica:
        - Para onde a liquidez está migrando
        - Quais incentive programs estão funcionando
        - Seasonal patterns
        - Correlation com market conditions
        """,
        "schedule": "6h",
        "queries": {
            "timescaledb": """
                WITH tvl_changes AS (
                    SELECT
                        protocol_id,
                        chain_id,
                        tvl_usd,
                        LAG(tvl_usd) OVER (
                            PARTITION BY protocol_id, chain_id
                            ORDER BY timestamp
                        ) as prev_tvl,
                        timestamp
                    FROM protocol_metrics
                    WHERE timestamp > NOW() - INTERVAL '7 days'
                )
                SELECT
                    protocol_id,
                    chain_id,
                    SUM(tvl_usd - COALESCE(prev_tvl, 0)) as net_flow,
                    AVG(tvl_usd) as avg_tvl,
                    STDDEV(tvl_usd) as tvl_volatility
                FROM tvl_changes
                GROUP BY protocol_id, chain_id
                HAVING ABS(SUM(tvl_usd - COALESCE(prev_tvl, 0))) > 1000000
                ORDER BY ABS(net_flow) DESC
            """,
            "neo4j": """
                MATCH (p:Protocol)-[d:DEPLOYED_ON]->(c:Chain)
                WHERE d.tvl_usd > 1000000
                WITH p, c, d.tvl_usd as current_tvl,
                     d.tvl_usd_7d_ago as prev_tvl
                WHERE abs(current_tvl - prev_tvl) / prev_tvl > 0.1
                RETURN p.name, c.name,
                       current_tvl, prev_tvl,
                       (current_tvl - prev_tvl) / prev_tvl as pct_change
                ORDER BY abs(pct_change) DESC
            """
        }
    },

    "dependency_risk_cascade": {
        "description": """
        Análise de risco em cascata: se um componente falha,
        qual o blast radius?
        """,
        "schedule": "daily",
        "scenarios": [
            {
                "name": "chainlink_oracle_failure",
                "trigger": "Chainlink oracle stops updating",
                "query": """
                    MATCH (p:Protocol)-[:DEPENDS_ON]->(o:Protocol {name: 'Chainlink'})
                    WITH p, p.metrics.tvl_usd as at_risk_tvl
                    OPTIONAL MATCH (p2:Protocol)-[:DEPENDS_ON]->(p)
                    WITH p, at_risk_tvl,
                         COLLECT(DISTINCT p2.name) as downstream,
                         SUM(p2.metrics.tvl_usd) as downstream_tvl
                    RETURN p.name, at_risk_tvl,
                           downstream, downstream_tvl,
                           at_risk_tvl + COALESCE(downstream_tvl, 0) as total_blast_radius
                    ORDER BY total_blast_radius DESC
                """
            },
            {
                "name": "usdc_depeg",
                "trigger": "USDC loses peg significantly (>2%)",
            },
            {
                "name": "ethereum_l1_congestion",
                "trigger": "Gas >500 gwei sustained for 1h",
            },
            {
                "name": "major_bridge_exploit",
                "trigger": "Bridge with >$100M TVL compromised",
            },
            {
                "name": "lido_steth_depeg",
                "trigger": "stETH depegs >3% from ETH",
            },
            {
                "name": "eigenlayer_slashing_cascade",
                "trigger": "Major slashing event on restaking",
            },
        ]
    },

    "developer_ecosystem_vitality": {
        "description": """
        Análise profunda da saúde do ecossistema de desenvolvimento.
        Baseado em dados do GitHub + package registries.
        """,
        "schedule": "weekly",
        "analyses": [
            {
                "name": "ecosystem_developer_count",
                "description": "Monthly active developers per ecosystem",
                "methodology": """
                    1. Map repos to ecosystems (electric_capital mapping)
                    2. Count unique commit authors per month
                    3. Classify: full-time (>10 commits/month),
                       part-time (2-10), one-time (1)
                    4. Track cohort retention
                """
            },
            {
                "name": "developer_migration",
                "description": "Developers moving between ecosystems",
                "methodology": """
                    1. Track contributors across ecosystem boundaries
                    2. Identify migration patterns: Ethereum→Solana, etc.
                    3. Calculate net developer flow
                    4. Correlate with funding events, grants programs
                """
            },
            {
                "name": "framework_adoption",
                "description": "Adoption trends of dev frameworks",
                "track": [
                    "foundry vs hardhat vs truffle",
                    "viem vs ethers.js vs web3.js",
                    "rust (solana/substrate) vs solidity vs move vs cairo",
                    "anchor vs native solana",
                    "cosmwasm vs cosmos SDK native",
                ]
            },
            {
                "name": "repo_quality_scoring",
                "description": "Automated quality assessment",
                "criteria": [
                    "has_tests (test/ directory exists)",
                    "has_ci (github actions/workflows)",
                    "has_docs (docs/ or README quality)",
                    "has_license",
                    "has_security_policy",
                    "dependency_freshness",
                    "code_review_culture (PR merge patterns)",
                    "bus_factor (contributor concentration)",
                ]
            },
        ]
    },

    "mev_landscape_analysis": {
        "description": """
        Análise completa do ecossistema MEV:
        - Extração por tipo (sandwich, arb, liquidation, JIT)
        - Builder market share
        - Censorship metrics
        - PBS health indicators
        """,
        "schedule": "daily",
        "data_sources": [
            "flashbots_transparency",
            "mev_boost_relays",
            "zeromev",
            "eigenphi",
            "libmev",
            "payload_de",
            "inclusion_watch",
        ],
        "metrics": [
            "total_mev_extracted_24h_eth",
            "mev_by_type_breakdown",
            "builder_market_hhi",           # Herfindahl index
            "top_5_builder_share_pct",
            "relay_market_share",
            "ofac_compliant_blocks_pct",    # Censorship metric
            "median_inclusion_delay_slots",
            "proposer_payment_median_eth",
            "searcher_to_builder_ratio",
            "mev_share_redistribution_pct",
        ]
    },

    "stablecoin_monitor": {
        "description": """
        Monitoramento contínuo do ecossistema de stablecoins.
        Early warning system para depegs.
        """,
        "schedule": "15min",
        "stablecoins_tracked": [
            "USDT", "USDC", "DAI", "FRAX", "LUSD",
            "GHO", "crvUSD", "PYUSD", "USDe", "FDUSD",
            "sDAI", "sUSDe", "USDD", "TUSD", "USDP",
        ],
        "metrics": [
            "peg_deviation_bps",
            "dex_liquidity_depth",
            "redemption_volume_24h",
            "backing_ratio",
            "backing_composition",
            "cross_chain_supply_distribution",
            "concentration_by_holder",
            "mint_burn_velocity",
        ],
        "alerts": {
            "depeg_warning": "abs(peg_deviation_bps) > 50",
            "depeg_critical": "abs(peg_deviation_bps) > 200",
            "liquidity_drain": "dex_liquidity_change_1h < -20%",
            "whale_redemption": "single_redemption > 1% of supply",
        }
    },

    "l2_comparative_analysis": {
        "description": """
        Comparação profunda entre L2s em todas as dimensões.
        """,
        "schedule": "daily",
        "l2s_tracked": [
            "arbitrum", "optimism", "base", "zksync_era",
            "starknet", "polygon_zkevm", "scroll", "linea",
            "mantle", "blast", "mode", "manta", "metis",
            "zora", "taiko",
        ],
        "comparison_dimensions": {
            "adoption": [
                "daily_active_addresses",
                "daily_transactions",
                "tvl_usd",
                "unique_contracts_deployed",
                "new_addresses_daily",
            ],
            "economics": [
                "l2_fee_revenue",
                "l1_data_costs",
                "sequencer_profit",
                "token_incentive_spend",
                "cost_per_transaction",
            ],
            "technology": [
                "proof_system",
                "data_availability_solution",
                "finality_time",
                "l2beat_stage",
                "fraud_proof_status",
                "forced_withdrawal_enabled",
                "proposer_decentralization",
                "sequencer_decentralization",
            ],
            "ecosystem": [
                "number_of_protocols",
                "number_of_developers",
                "native_dapps_count",
                "bridge_tvl_inflows",
                "grant_program_size",
            ],
        }
    },

    "governance_intelligence": {
        "description": """
        Monitoramento de governança cross-protocol.
        Detectar tendências, conflitos, oportunidades.
        """,
        "schedule": "6h",
        "analyses": [
            "active_proposals_summary",
            "voting_power_concentration_trend",
            "delegate_activity_scorecard",
            "cross_dao_voting_correlation",
            "proposal_topic_clustering",     # LLM-based topic extraction
            "treasury_spending_analysis",
            "governance_attack_risk_assessment",
            "quorum_health_check",
        ]
    },

    "zk_technology_tracker": {
        "description": """
        Tracking the ZK technology landscape:
        - Proof system benchmarks
        - New cryptographic primitives
        - ZK application patterns
        - Prover hardware requirements
        """,
        "schedule": "weekly",
        "proof_systems_tracked": [
            "groth16", "plonk", "halo2", "stark",
            "plonky2", "plonky3", "nova", "supernova",
            "hyperplonk", "binius", "circle_starks",
            "sp1", "risc0", "jolt", "nexus",
        ],
        "metrics": [
            "proof_generation_time",
            "verification_gas_cost",
            "proof_size_bytes",
            "trusted_setup_required",
            "post_quantum_security",
            "recursion_support",
            "gpu_acceleration_support",
            "github_activity_trend",
            "adoption_count_protocols",
        ]
    },
}
