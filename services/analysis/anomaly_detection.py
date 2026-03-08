# services/analysis/anomaly_detection.py

"""
ANOMALY DETECTION — Detecção automatizada de eventos anômalos
"""

ANOMALY_DETECTORS = {

    "price_anomaly": {
        "description": "Detecta movimentos de preço anômalos",
        "methods": [
            {
                "name": "zscore_rolling",
                "window": "24h",
                "threshold": 3.0,
                "metric": "price_usd",
            },
            {
                "name": "volume_price_divergence",
                "description": "Preço move sem volume correspondente",
                "threshold": "price_change > 5% AND volume_change < 20%",
            },
            {
                "name": "cross_exchange_divergence",
                "description": "Preço diverge entre exchanges",
                "threshold": "max_deviation > 2%",
            },
        ]
    },

    "tvl_anomaly": {
        "description": "Detecta mudanças bruscas em TVL",
        "methods": [
            {
                "name": "sudden_drop",
                "threshold": "tvl_change_1h < -10%",
                "severity": "critical",
                "possible_causes": [
                    "exploit", "depeg", "whale_withdrawal",
                    "smart_contract_migration", "data_error"
                ],
            },
            {
                "name": "suspicious_inflow",
                "threshold": "tvl_change_1h > 50%",
                "severity": "warning",
                "possible_causes": [
                    "airdrop_farming", "legitimate_growth",
                    "wash_trading", "incentive_launch"
                ],
            },
        ]
    },

    "governance_anomaly": {
        "description": "Detecta atividade incomum em governança",
        "methods": [
            {
                "name": "voting_power_accumulation",
                "description": "Grande acúmulo de voting power antes de vote",
                "threshold": "delegation_change > 5% of supply in 24h",
            },
            {
                "name": "last_minute_vote_swing",
                "description": "Resultado muda nas últimas horas",
                "threshold": "vote_swing > 20% in last 10% of voting period",
            },
            {
                "name": "flash_loan_governance",
                "description": "Borrowed tokens used for voting",
            },
        ]
    },

    "developer_anomaly": {
        "description": "Detecta mudanças incomuns em dev activity",
        "methods": [
            {
                "name": "dev_exodus",
                "description": "Multiple core devs stop committing",
                "threshold": "core_contributors_active_30d drops > 30%",
                "severity": "high",
            },
            {
                "name": "suspicious_commit_pattern",
                "description": "Artificial commit inflation",
                "indicators": [
                    "many_empty_commits",
                    "auto_generated_commits",
                    "single_author_burst",
                ],
            },
        ]
    },

    "security_anomaly": {
        "description": "Early warning para security events",
        "methods": [
            {
                "name": "unusual_contract_interaction",
                "description": "Padrão de interação atípico com contratos",
                "indicators": [
                    "new_address_large_approval",
                    "admin_function_call",
                    "proxy_upgrade_without_governance",
                    "flash_loan_interaction_spike",
                ],
            },
            {
                "name": "bridge_anomaly",
                "description": "Fluxo atípico em bridges",
                "threshold": "bridge_volume_1h > 10x median",
            },
        ]
    },

    "on_chain_anomaly": {
        "description": "Anomalias em métricas on-chain",
        "methods": [
            {
                "name": "gas_price_spike",
                "threshold": "gas_price > 5x 24h_median",
            },
            {
                "name": "mempool_congestion",
                "threshold": "pending_txs > 3x average",
            },
            {
                "name": "validator_behavior",
                "indicators": [
                    "missed_attestations_spike",
                    "slashing_event",
                    "proposer_missed_block_rate",
                ],
            },
            {
                "name": "token_supply_change",
                "description": "Unexpected mint/burn events",
                "threshold": "supply_change > 0.1% in single tx",
            },
        ]
    },
}
