# config/protocol_universe.py

"""
PROTOCOL UNIVERSE — Lista master de TUDO que o sistema monitora
Organizado por categoria e prioridade
"""

PROTOCOL_UNIVERSE = {

    # ═══════════════════════════════════════════
    # LAYER 1 BLOCKCHAINS
    # ═══════════════════════════════════════════

    "l1_blockchains": {
        "priority": "CRITICAL",
        "protocols": {
            "ethereum": {
                "chain_id": "1",
                "consensus": "pos_gasper",
                "vm": "evm",
                "focus_areas": [
                    "validator_economics", "blob_market",
                    "staking_ratio", "client_diversity",
                    "eip_pipeline", "mev_pbs",
                    "issuance_burn_dynamics",
                ],
            },
            "bitcoin": {
                "focus_areas": [
                    "hashrate", "difficulty", "fee_market",
                    "lightning_network", "ordinals_brc20",
                    "miner_economics", "utxo_metrics",
                ],
            },
            "solana": {
                "focus_areas": [
                    "tps_actual", "vote_costs",
                    "validator_economics", "jito_mev",
                    "firedancer_progress", "compressed_nfts",
                    "state_compression", "local_fee_markets",
                ],
            },
            "cosmos_hub": {
                "focus_areas": [
                    "ibc_volume", "interchain_security",
                    "atom_staking", "governance_activity",
                    "connected_chains_count",
                ],
            },
            "polkadot": {
                "focus_areas": [
                    "parachain_auctions", "xcm_messages",
                    "dot_staking", "governance_opengov",
                    "coretime_market",
                ],
            },
            "avalanche": {
                "focus_areas": [
                    "subnet_growth", "c_chain_activity",
                    "validator_set", "teleporter_usage",
                ],
            },
            "near": {
                "focus_areas": [
                    "sharding_status", "account_abstraction",
                    "chain_signatures", "data_availability",
                ],
            },
            "sui": {
                "focus_areas": [
                    "move_adoption", "object_model_usage",
                    "validator_set", "defi_growth",
                ],
            },
            "aptos": {
                "focus_areas": [
                    "move_vm", "block_stm_performance",
                    "validator_set",
                ],
            },
            "ton": {
                "focus_areas": [
                    "telegram_integration", "jetton_ecosystem",
                    "sharding_utilization",
                ],
            },
            "sei": {},
            "injective": {},
            "celestia": {
                "focus_areas": [
                    "blob_usage", "rollup_clients",
                    "data_availability_pricing",
                ],
            },
            "monad": {"status": "pre_launch_tracking"},
            "berachain": {"status": "pre_launch_tracking"},
        }
    },

    # ═══════════════════════════════════════════
    # LAYER 2 / ROLLUPS
    # ═══════════════════════════════════════════

    "l2_rollups": {
        "priority": "CRITICAL",
        "protocols": {
            # Optimistic Rollups
            "arbitrum_one": {"type": "optimistic", "stack": "nitro"},
            "arbitrum_nova": {"type": "optimistic", "stack": "nitro_anytrust"},
            "optimism": {"type": "optimistic", "stack": "op_stack"},
            "base": {"type": "optimistic", "stack": "op_stack"},
            "blast": {"type": "optimistic", "stack": "op_stack_modified"},
            "mantle": {"type": "optimistic", "stack": "op_stack_modified"},
            "mode": {"type": "optimistic", "stack": "op_stack"},
            "metis": {"type": "optimistic", "stack": "custom"},
            "boba": {"type": "optimistic", "stack": "op_stack"},
            "world_chain": {"type": "optimistic", "stack": "op_stack"},
            "zora": {"type": "optimistic", "stack": "op_stack"},
            "fraxtal": {"type": "optimistic", "stack": "op_stack"},
            "redstone": {"type": "optimistic", "stack": "op_stack"},
            "cyber": {"type": "optimistic", "stack": "op_stack"},

            # ZK Rollups
            "zksync_era": {"type": "zk", "proof_system": "boojum"},
            "starknet": {"type": "zk", "proof_system": "stark"},
            "polygon_zkevm": {"type": "zk", "proof_system": "plonk"},
            "scroll": {"type": "zk", "proof_system": "halo2_kzg"},
            "linea": {"type": "zk", "proof_system": "custom_lattice"},
            "taiko": {"type": "zk", "proof_system": "multi_prover"},
            "zkfair": {"type": "zk"},
            "immutable_x": {"type": "validium", "proof_system": "stark"},

            # Superchain (OP Stack ecosystem)
            "_superchain_tracking": {
                "description": "Track OP Stack adoption as ecosystem",
                "metrics": [
                    "total_superchain_tvl",
                    "cross_chain_messages",
                    "shared_sequencer_progress",
                    "new_chain_deployments",
                ],
            },

            # Orbit (Arbitrum ecosystem)
            "_orbit_tracking": {
                "description": "Track Arbitrum Orbit chains",
                "metrics": [
                    "total_orbit_tvl",
                    "orbit_chain_count",
                    "custom_gas_tokens",
                ],
            },
        },
    },

    # ═══════════════════════════════════════════
    # DeFi PROTOCOLS — DEX
    # ═══════════════════════════════════════════

    "dex": {
        "priority": "HIGH",
        "protocols": {
            "uniswap": {
                "versions": ["v2", "v3", "v4"],
                "chains": ["ethereum", "polygon", "arbitrum", "optimism", "base", "bsc", "avalanche", "celo", "blast"],
                "focus": ["concentrated_liquidity", "hooks_v4", "uniswapx", "governance"],
            },
            "curve": {
                "focus": ["stableswap", "crvusd", "llamalend", "curve_wars", "ve_tokenomics"],
            },
            "balancer": {
                "versions": ["v2", "v3"],
                "focus": ["weighted_pools", "boosted_pools", "aura_integration"],
            },
            "aerodrome": {"chain": "base", "type": "ve33"},
            "velodrome": {"chain": "optimism", "type": "ve33"},
            "camelot": {"chain": "arbitrum"},
            "trader_joe": {"chains": ["avalanche", "arbitrum"]},
            "pancakeswap": {"chains": ["bsc", "ethereum", "arbitrum"]},
            "sushiswap": {},
            "maverick": {"focus": ["dynamic_distribution"]},

            # Solana DEXs
            "raydium": {"chain": "solana"},
            "orca": {"chain": "solana", "focus": ["whirlpools_cl"]},
            "jupiter": {"chain": "solana", "type": "aggregator"},
            "phoenix": {"chain": "solana", "type": "orderbook"},
            "drift": {"chain": "solana", "type": "perps_dex"},

            # Cosmos DEXs
            "osmosis": {"chain": "cosmos"},
            "astroport": {"chains": ["terra", "neutron", "injective"]},
        }
    },

    # ═══════════════════════════════════════════
    # DeFi — LENDING & BORROWING
    # ═══════════════════════════════════════════

    "lending": {
        "priority": "HIGH",
        "protocols": {
            "aave": {
                "versions": ["v2", "v3"],
                "chains": ["ethereum", "polygon", "avalanche", "arbitrum", "optimism", "base", "metis", "bsc", "gnosis", "scroll"],
                "focus": ["gho_stablecoin", "risk_parameters", "governance", "flash_loans"],
            },
            "compound": {
                "versions": ["v2", "v3"],
                "focus": ["single_asset_model_v3", "governance"],
            },
            "morpho": {
                "focus": ["morpho_blue", "isolated_markets", "curated_vaults"],
            },
            "spark": {"focus": ["makerdao_integration", "sdai"]},
            "venus": {"chain": "bsc"},
            "benqi": {"chain": "avalanche"},
            "radiant": {"chains": ["arbitrum", "bsc"]},
            "silo": {"focus": ["isolated_markets"]},
            "euler": {"versions": ["v2"], "focus": ["modular_lending"]},
            "kamino": {"chain": "solana"},
            "marginfi": {"chain": "solana"},
            "solend": {"chain": "solana"},
        }
    },

    # ═══════════════════════════════════════════
    # DeFi — CDP / STABLECOINS
    # ═══════════════════════════════════════════

    "cdp_stablecoins": {
        "priority": "HIGH",
        "protocols": {
            "makerdao": {
                "focus": ["dai_supply", "rwa_exposure", "endgame_plan", "subDAOs", "dsr_rate", "spark_integration"],
            },
            "liquity": {
                "versions": ["v1", "v2"],
                "focus": ["lusd_peg", "redemption_mechanics", "v2_design"],
            },
            "ethena": {
                "focus": ["usde_mechanism", "basis_trade", "sUSDe_yield", "risk_analysis", "reserve_fund"],
            },
            "frax": {
                "focus": ["frax_stablecoin", "frxeth", "fraxlend", "fraxtal_l2"],
            },
            "crvusd": {"focus": ["llamma_mechanism", "soft_liquidations"]},
            "gho": {"focus": ["aave_integration", "facilitators"]},
            "raft": {},
            "prisma": {},
        }
    },

    # ═══════════════════════════════════════════
    # LIQUID STAKING & RESTAKING
    # ═══════════════════════════════════════════

    "staking_restaking": {
        "priority": "HIGH",
        "protocols": {
            "lido": {
                "focus": [
                    "steth_dominance", "validator_set",
                    "node_operator_diversity", "governance",
                    "steth_defi_integrations", "v2_withdrawals",
                ],
            },
            "rocketpool": {
                "focus": ["reth", "minipool_operators", "decentralization"],
            },
            "eigenlayer": {
                "focus": [
                    "restaked_tvl", "avs_ecosystem",
                    "operator_set", "slashing_conditions",
                    "eigenda", "rewards_distribution",
                ],
            },
            "ether_fi": {"focus": ["eeth", "liquid_restaking"]},
            "puffer": {"focus": ["pufeth", "native_restaking"]},
            "renzo": {"focus": ["ezeth"]},
            "kelp": {"focus": ["rseth"]},
            "swell": {"focus": ["sweth", "restaking"]},
            "mantle_lsp": {"focus": ["meth"]},
            "coinbase_cbeth": {},
            "frax_eth": {},
            "stakewise": {},
            "stader": {},
            "jito": {"chain": "solana", "focus": ["jitosol", "mev_staking"]},
            "marinade": {"chain": "solana"},
            "blaze_stake": {"chain": "solana"},

            # Symbiotic (EigenLayer competitor)
            "symbiotic": {
                "status": "early_stage",
                "focus": ["restaking_alternative", "design_differences"],
            },

            # Karak
            "karak": {
                "focus": ["restaking", "dss_model"],
            },
        }
    },

    # ═══════════════════════════════════════════
    # BRIDGES & INTEROPERABILITY
    # ═══════════════════════════════════════════

    "bridges_interop": {
        "priority": "HIGH",
        "protocols": {
            "wormhole": {"focus": ["messaging", "ntt", "multichain_governance"]},
            "layerzero": {"focus": ["omnichain_messaging", "oft_standard", "dvn_model"]},
            "axelar": {"focus": ["gmp", "interchain_token", "cosmos_integration"]},
            "chainlink_ccip": {"focus": ["cross_chain_messaging", "token_transfers"]},
            "across": {"focus": ["intent_based", "uma_oracle"]},
            "stargate": {"focus": ["unified_liquidity", "layerzero_native"]},
            "hop": {"focus": ["rollup_native"]},
            "synapse": {},
            "celer": {},
            "multichain": {"status": "post_mortem_tracking"},
            "debridge": {},
            "hyperlane": {"focus": ["permissionless_interop", "sovereign_consensus"]},
            "ibc": {"focus": ["cosmos_native", "channel_activity", "packet_forwarding"]},
            "polymer": {"focus": ["ibc_on_ethereum"]},
            "union": {"focus": ["zk_ibc"]},
        }
    },

    # ═══════════════════════════════════════════
    # ORACLES
    # ═══════════════════════════════════════════

    "oracles": {
        "priority": "HIGH",
        "protocols": {
            "chainlink": {
                "focus": [
                    "price_feeds", "vrf", "automation", "ccip",
                    "functions", "data_streams",
                    "feed_coverage", "node_operator_set",
                ],
            },
            "pyth": {"focus": ["pull_oracle", "solana_native", "cross_chain"]},
            "chronicle": {"focus": ["makerdao_native", "scribe"]},
            "redstone": {"focus": ["modular_oracle", "evm_connector"]},
            "api3": {"focus": ["first_party_oracles", "dapis"]},
            "uma": {"focus": ["optimistic_oracle", "across_integration"]},
            "fluxprotocol": {},
            "switchboard": {"chain": "solana"},
        }
    },

    # ═══════════════════════════════════════════
    # DERIVATIVES & PERPS
    # ═══════════════════════════════════════════

    "derivatives": {
        "priority": "MEDIUM",
        "protocols": {
            "gmx": {"chains": ["arbitrum", "avalanche"], "versions": ["v1", "v2"]},
            "dydx": {"versions": ["v3_ethereum", "v4_cosmos"]},
            "synthetix": {"versions": ["v2", "v3"], "focus": ["perps_v3", "andromeda"]},
            "hyperliquid": {"focus": ["orderbook_l1", "hlp"]},
            "vertex": {"chain": "arbitrum"},
            "aevo": {},
            "lyra": {"focus": ["options"]},
            "dopex": {"focus": ["options"]},
            "hegic": {"focus": ["options"]},
            "ribbon": {"focus": ["structured_products"]},
            "kwenta": {"chain": "optimism", "focus": ["synthetix_frontend"]},
            "perennial": {},
        }
    },

    # ═══════════════════════════════════════════
    # INFRASTRUCTURE & TOOLING
    # ═══════════════════════════════════════════

    "infrastructure": {
        "priority": "MEDIUM",
        "protocols": {
            "the_graph": {"focus": ["subgraph_queries", "indexer_economics", "migration_to_L2"]},
            "ens": {"focus": ["registrations", "renewals", "governance", "v2"]},
            "filecoin": {"focus": ["storage_deals", "fil_plus"]},
            "arweave": {"focus": ["permanent_storage", "ao_compute"]},
            "livepeer": {"focus": ["transcoding_network"]},
            "gelato": {"focus": ["automation", "relay"]},
            "safe": {"focus": ["multisig_usage", "modules"]},
            "gnosis_chain": {"focus": ["xdai", "validators"]},
            "worldcoin": {"focus": ["world_id", "orb_verification"]},
            "eas": {"focus": ["attestation_schema_adoption"]},
        }
    },

    # ═══════════════════════════════════════════
    # EMERGING / WATCHING
    # ═══════════════════════════════════════════

    "emerging_watch": {
        "priority": "LOW",
        "description": "Protocolos/tecnologias emergentes para monitorar",
        "categories": {
            "intent_based_architectures": [
                "across", "uniswapx", "cow_protocol",
                "essential", "anoma", "flashbots_suave",
            ],
            "account_abstraction": [
                "erc4337_bundlers", "biconomy", "zerodev",
                "pimlico", "stackup", "alchemy_aa",
            ],
            "real_world_assets": [
                "ondo", "centrifuge", "maple", "goldfinch",
                "backed", "matrixdock", "mountain_protocol",
            ],
            "decentralized_ai": [
                "bittensor", "render", "akash",
                "ritual", "gensyn", "modulus",
                "ora_protocol",
            ],
            "social_protocols": [
                "farcaster", "lens", "deso",
                "cyber", "friend_tech",
            ],
            "payment_channels": [
                "lightning_network", "state_channels",
                "payment_rollups",
            ],
            "privacy": [
                "aztec", "railgun", "tornado_cash_analysis",
                "penumbra", "namada", "zcash",
            ],
            "fhe_mpc": [
                "zama", "sunscreen", "fhenix",
                "inco_network",
            ],
            "parallel_execution": [
                "monad", "sei_v2", "fuel",
                "movement_labs",
            ],
        }
    },
}
