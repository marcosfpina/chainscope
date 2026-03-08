# services/collector/source_taxonomy.py

"""
CHAINSCOPE — Source Taxonomy
Cada fonte é classificada por:
  - Confiabilidade (reliability_score)
  - Tipo de dado (data_type)
  - Latência típica (typical_latency)
  - Método de coleta (collection_method)
"""

SOURCE_TAXONOMY = {

    # ═══════════════════════════════════════════
    # TIER 1: FONTES PRIMÁRIAS ON-CHAIN (Verdade Ground Truth)
    # Confiabilidade: 0.95-1.0
    # ═══════════════════════════════════════════

    "on_chain_direct": {
        "description": "Dados diretos de nodes/RPCs — a fonte mais confiável",
        "reliability_score": 0.99,
        "sources": {

            # ── Ethereum Ecosystem ──
            "ethereum_rpc": {
                "endpoints": [
                    # Públicos (rate limited)
                    "https://eth.llamarpc.com",
                    "https://rpc.ankr.com/eth",
                    "https://ethereum.publicnode.com",
                    "https://1rpc.io/eth",
                    "https://rpc.flashbots.net",
                ],
                "data_types": [
                    "blocks", "transactions", "receipts", "logs",
                    "state", "traces", "pending_txs"
                ],
                "collection_method": "json_rpc",
                "rate_limit": "varies_by_provider",
                "notes": "Rodar próprio node é ideal para volume alto"
            },

            "ethereum_beacon": {
                "endpoints": [
                    "https://beaconcha.in/api/v1",
                    "https://eth2.public-rpc.com",
                ],
                "data_types": [
                    "validators", "attestations", "slots",
                    "epochs", "committees", "sync_committees",
                    "proposer_duties", "slashings"
                ],
                "collection_method": "rest_api + sse_events",
            },

            # ── Bitcoin ──
            "bitcoin_rpc": {
                "endpoints": [
                    "https://blockstream.info/api",
                    "https://mempool.space/api",
                ],
                "data_types": [
                    "blocks", "transactions", "utxo_set",
                    "mempool", "fee_estimates", "difficulty"
                ],
                "collection_method": "rest_api",
            },

            # ── Solana ──
            "solana_rpc": {
                "endpoints": [
                    "https://api.mainnet-beta.solana.com",
                    "https://rpc.ankr.com/solana",
                    "https://solana.publicnode.com",
                ],
                "data_types": [
                    "blocks", "transactions", "accounts",
                    "program_accounts", "token_accounts",
                    "vote_accounts", "stake_accounts",
                    "slot_leaders", "epoch_info"
                ],
                "collection_method": "json_rpc + websocket",
            },

            # ── Cosmos Ecosystem ──
            "cosmos_lcd": {
                "endpoints": [
                    "https://rest.cosmos.directory/{chain}",
                    "https://api.cosmos.network",
                ],
                "data_types": [
                    "blocks", "transactions", "validators",
                    "governance_proposals", "staking",
                    "ibc_channels", "ibc_connections",
                    "wasm_contracts", "bank_supply"
                ],
                "chain_registry": "https://github.com/cosmos/chain-registry",
                "collection_method": "rest_api + grpc + websocket",
            },

            # ── Polkadot/Substrate ──
            "polkadot_rpc": {
                "endpoints": [
                    "wss://rpc.polkadot.io",
                    "wss://kusama-rpc.polkadot.io",
                    "https://polkadot.api.subscan.io",
                ],
                "data_types": [
                    "blocks", "extrinsics", "events",
                    "parachains", "auctions", "crowdloans",
                    "staking", "nominations", "councils",
                    "referenda", "xcm_messages"
                ],
                "collection_method": "substrate_rpc + websocket",
            },

            # ── Avalanche ──
            "avalanche_rpc": {
                "endpoints": [
                    "https://api.avax.network",
                    "https://rpc.ankr.com/avalanche",
                ],
                "data_types": [
                    "x_chain_txs", "p_chain_validators",
                    "c_chain_blocks", "subnets",
                    "delegations", "rewards"
                ],
            },

            # ── Near Protocol ──
            "near_rpc": {
                "endpoints": [
                    "https://rpc.mainnet.near.org",
                    "https://archival-rpc.mainnet.near.org",
                ],
                "data_types": [
                    "blocks", "chunks", "transactions",
                    "receipts", "accounts", "access_keys",
                    "validators", "protocol_config"
                ],
            },

            # ── Arbitrum, Optimism, Base, zkSync, StarkNet... ──
            "l2_rpcs": {
                "arbitrum": "https://arb1.arbitrum.io/rpc",
                "optimism": "https://mainnet.optimism.io",
                "base": "https://mainnet.base.org",
                "zksync": "https://mainnet.era.zksync.io",
                "starknet": "https://starknet-mainnet.public.blastapi.io",
                "polygon_zkevm": "https://zkevm-rpc.com",
                "scroll": "https://rpc.scroll.io",
                "linea": "https://rpc.linea.build",
                "mantle": "https://rpc.mantle.xyz",
                "blast": "https://rpc.blast.io",
                "mode": "https://mainnet.mode.network",
                "data_types": ["evm_compatible + L2_specific"],
            },
        }
    },

    # ═══════════════════════════════════════════
    # TIER 1.5: INDEXADORES ON-CHAIN (Dados processados de alta confiança)
    # Confiabilidade: 0.90-0.95
    # ═══════════════════════════════════════════

    "on_chain_indexed": {
        "description": "Indexadores que processam dados on-chain brutos",
        "reliability_score": 0.93,
        "sources": {

            "the_graph": {
                "endpoint": "https://gateway.thegraph.com/api/{key}/subgraphs/id/{id}",
                "description": "Subgraphs descentralizados — milhares de protocolos indexados",
                "explorer": "https://thegraph.com/explorer",
                "data_types": [
                    "protocol_specific_events", "aggregated_metrics",
                    "historical_state", "entity_relationships"
                ],
                "key_subgraphs": [
                    "uniswap-v3", "aave-v3", "compound-v3",
                    "lido", "maker", "curve", "balancer",
                    "ens", "gitcoin", "hop-protocol"
                ],
                "collection_method": "graphql",
            },

            "dune_analytics": {
                "endpoint": "https://api.dune.com/api/v1",
                "description": "SQL queries sobre dados on-chain indexados",
                "data_types": [
                    "custom_analytics", "protocol_metrics",
                    "wallet_analytics", "defi_tvl",
                    "nft_analytics", "gas_analytics"
                ],
                "collection_method": "rest_api",
                "notes": "Agendar queries e cachear resultados"
            },

            "flipside": {
                "endpoint": "https://api-v2.flipsidecrypto.xyz",
                "description": "Similar ao Dune — dados multi-chain",
                "chains": [
                    "ethereum", "polygon", "arbitrum", "optimism",
                    "avalanche", "bsc", "solana", "near", "flow",
                    "cosmos", "axelar", "sei", "base", "blast"
                ],
                "collection_method": "rest_api + sql",
            },

            "allium": {
                "endpoint": "https://api.allium.so",
                "description": "Enterprise blockchain data — 40+ chains",
                "collection_method": "rest_api + sql",
            },

            "subsquid": {
                "endpoint": "https://app.subsquid.io",
                "description": "Indexador decentralizado multi-chain",
                "collection_method": "graphql",
            },

            "goldsky": {
                "endpoint": "https://api.goldsky.com",
                "description": "Subgraphs + Mirror pipelines",
                "collection_method": "graphql + streaming",
            },

            "nansen_public": {
                "endpoint": "https://query.nansen.ai",
                "description": "Smart money labels, entity tracking",
                "collection_method": "rest_api",
            },

            "arkham_intel": {
                "endpoint": "https://api.arkhamintelligence.com",
                "description": "Entity intelligence, wallet labels",
                "collection_method": "rest_api",
            },

            "chainalysis_free": {
                "endpoint": "https://public.chainalysis.com",
                "description": "Sanctions lists, OFAC addresses",
                "collection_method": "rest_api",
            },
        }
    },

    # ═══════════════════════════════════════════
    # TIER 2: PROTOCOL DATA AGGREGATORS
    # Confiabilidade: 0.85-0.92
    # ═══════════════════════════════════════════

    "protocol_aggregators": {
        "description": "Agregadores que normalizam dados de múltiplos protocolos",
        "reliability_score": 0.88,
        "sources": {

            "defillama": {
                "base_url": "https://api.llama.fi",
                "endpoints": {
                    "tvl": "/v2/protocols",
                    "tvl_historical": "/v2/historicalChainTvl/{chain}",
                    "protocol_detail": "/protocol/{protocol}",
                    "yields": "/pools",  # yields.llama.fi
                    "stablecoins": "/stablecoins",  # stablecoins.llama.fi
                    "bridges": "/bridges",  # bridges.llama.fi
                    "volumes_dex": "/overview/dexs",  # api.llama.fi/overview/dexs
                    "volumes_derivatives": "/overview/derivatives",
                    "fees_revenue": "/overview/fees",
                    "options": "/overview/options",
                    "liquidations": "/overview/liquidations",
                    "raises": "/raises",  # fundraising rounds
                    "hacks": "/hacks",  # security incidents
                    "treasury": "/treasury/{protocol}",
                    "governance": "/governance/{protocol}",
                    "emissions": "/emissions/{protocol}",
                    "active_users": "/activeUsers/{chain}",
                    "nfts_collection": "/nfts/collection/{collection}",
                    "coins_prices": "/prices/current/{chain}:{address}",
                    "coins_historical": "/coins/prices/historical/{timestamp}/{chain}:{address}",
                },
                "rate_limit": "reasonable_use",
                "collection_method": "rest_api",
                "notes": "FONTE PRIMÁRIA para TVL, volumes, fees. Open source e transparente."
            },

            "coingecko": {
                "base_url": "https://api.coingecko.com/api/v3",
                "endpoints": {
                    "coins_list": "/coins/list",
                    "coin_detail": "/coins/{id}",
                    "market_chart": "/coins/{id}/market_chart",
                    "ohlc": "/coins/{id}/ohlc",
                    "exchanges": "/exchanges",
                    "exchange_volume": "/exchanges/{id}/volume_chart",
                    "categories": "/coins/categories",
                    "trending": "/search/trending",
                    "global": "/global",
                    "global_defi": "/global/decentralized_finance_defi",
                    "derivatives": "/derivatives",
                    "asset_platforms": "/asset_platforms",
                },
                "rate_limit": "10-30 req/min (free tier)",
                "collection_method": "rest_api",
            },

            "coinmarketcap": {
                "base_url": "https://pro-api.coinmarketcap.com/v2",
                "endpoints": {
                    "listings": "/cryptocurrency/listings/latest",
                    "quotes": "/cryptocurrency/quotes/latest",
                    "metadata": "/cryptocurrency/info",
                    "global_metrics": "/global-metrics/quotes/latest",
                    "exchange_listings": "/exchange/listings/latest",
                },
                "collection_method": "rest_api",
            },

            "token_terminal": {
                "base_url": "https://api.tokenterminal.com/v2",
                "data_types": [
                    "revenue", "earnings", "fees",
                    "tvl", "active_users", "token_incentives",
                    "market_cap_to_revenue", "pe_ratio",
                    "protocol_fundamentals"
                ],
                "collection_method": "rest_api",
                "notes": "Excelente para métricas financeiras de protocolos"
            },

            "messari": {
                "base_url": "https://data.messari.io/api",
                "endpoints": {
                    "assets": "/v2/assets",
                    "asset_profile": "/v2/assets/{asset}/profile",
                    "asset_metrics": "/v1/assets/{asset}/metrics",
                    "markets": "/v1/markets",
                    "news": "/v1/news",
                },
                "data_types": [
                    "asset_profiles", "sector_classification",
                    "governance_details", "token_economics",
                    "technology_overview"
                ],
                "collection_method": "rest_api",
            },

            "l2beat": {
                "base_url": "https://api.l2beat.com",
                "data_types": [
                    "l2_tvl", "l2_risk_analysis",
                    "l2_technology_details", "l2_permissions",
                    "l2_milestones", "da_layer_analysis",
                    "bridge_risk_scores", "stage_classification"
                ],
                "collection_method": "rest_api + github_scrape",
                "github": "https://github.com/l2beat/l2beat",
                "notes": "FONTE DEFINITIVA para análise de L2s e bridges"
            },

            "electric_capital_dev_report": {
                "url": "https://github.com/electric-capital/crypto-ecosystems",
                "data_types": ["developer_ecosystem_mapping", "repo_classification"],
                "collection_method": "github_api",
                "notes": "Mapeamento de repos por ecossistema — atualizado pela comunidade"
            },
        }
    },

    # ═══════════════════════════════════════════
    # TIER 2.5: MARKET MICROSTRUCTURE
    # Confiabilidade: 0.85-0.95
    # ═══════════════════════════════════════════

    "market_microstructure": {
        "description": "Dados de exchanges, orderbooks, funding rates",
        "reliability_score": 0.90,
        "sources": {

            "ccxt_unified": {
                "description": "Biblioteca unificada — 100+ exchanges",
                "library": "ccxt",
                "data_types": [
                    "ohlcv", "orderbook", "trades", "tickers",
                    "funding_rates", "open_interest",
                    "liquidations", "exchange_info"
                ],
                "priority_exchanges": [
                    "binance", "coinbase", "okx", "bybit",
                    "kraken", "deribit", "htx", "kucoin",
                    "bitfinex", "gate", "mexc"
                ],
                "collection_method": "rest + websocket via ccxt",
            },

            "kaiko": {
                "base_url": "https://us.market-api.kaiko.io",
                "data_types": [
                    "trades", "ohlcv", "orderbook_snapshots",
                    "vwap", "exchange_metrics", "slippage",
                    "market_depth", "cross_exchange_arbitrage"
                ],
                "collection_method": "rest_api + streaming",
            },

            "coinalyze": {
                "base_url": "https://api.coinalyze.net/v1",
                "data_types": [
                    "open_interest", "funding_rates",
                    "liquidations", "long_short_ratio",
                    "futures_volumes"
                ],
                "collection_method": "rest_api",
            },

            "laevitas": {
                "description": "Derivatives analytics — options, futures",
                "data_types": [
                    "options_flow", "options_oi", "volatility_surface",
                    "term_structure", "greeks", "max_pain",
                    "put_call_ratio", "gamma_exposure"
                ],
                "collection_method": "rest_api",
            },

            "dex_aggregator_data": {
                "sources": {
                    "0x_api": "https://api.0x.org",
                    "1inch_api": "https://api.1inch.dev",
                    "paraswap_api": "https://apiv5.paraswap.io",
                    "jupiter_api": "https://quote-api.jup.ag/v6",  # Solana
                    "cow_protocol": "https://api.cow.fi",
                },
                "data_types": [
                    "swap_quotes", "routing_data",
                    "liquidity_sources", "price_impact",
                    "gas_estimates"
                ],
            },
        }
    },

    # ═══════════════════════════════════════════
    # TIER 3: GOVERNANCE & DAO DATA
    # Confiabilidade: 0.85-0.92
    # ═══════════════════════════════════════════

    "governance": {
        "description": "Proposals, votações, delegação",
        "reliability_score": 0.90,
        "sources": {

            "snapshot": {
                "endpoint": "https://hub.snapshot.org/graphql",
                "data_types": [
                    "spaces", "proposals", "votes",
                    "strategies", "delegation"
                ],
                "collection_method": "graphql",
                "notes": "Off-chain voting — maior plataforma de governance"
            },

            "tally": {
                "endpoint": "https://api.tally.xyz/query",
                "data_types": [
                    "on_chain_proposals", "votes",
                    "delegates", "organizations",
                    "governor_contracts"
                ],
                "collection_method": "graphql",
            },

            "boardroom": {
                "endpoint": "https://api.boardroom.info/v1",
                "data_types": [
                    "proposals", "votes", "voters",
                    "protocols", "stats"
                ],
                "collection_method": "rest_api",
            },

            "agora": {
                "description": "Governance platform — Optimism, ENS, etc.",
                "data_types": ["delegates", "proposals", "votes"],
                "collection_method": "rest_api",
            },

            "forum_scraping": {
                "targets": [
                    "https://forum.makerdao.com",
                    "https://governance.aave.com",
                    "https://forum.arbitrum.foundation",
                    "https://gov.optimism.io",
                    "https://forum.ens.domains",
                    "https://research.lido.fi",
                    "https://forum.compound.finance",
                    "https://forum.uniswap.org",
                    "https://forum.balancer.fi",
                ],
                "data_types": [
                    "discussion_threads", "temperature_checks",
                    "rfc_proposals", "sentiment"
                ],
                "collection_method": "discourse_api + html_parse",
                "notes": "Maioria usa Discourse — API padronizada"
            },
        }
    },

    # ═══════════════════════════════════════════
    # TIER 3: DEVELOPER ACTIVITY
    # Confiabilidade: 0.88-0.95
    # ═══════════════════════════════════════════

    "developer_activity": {
        "description": "Atividade de desenvolvimento — código, contribuições",
        "reliability_score": 0.92,
        "sources": {

            "github_api": {
                "endpoint": "https://api.github.com",
                "data_types": [
                    "repos", "commits", "pull_requests",
                    "issues", "releases", "contributors",
                    "stars", "forks", "code_frequency",
                    "commit_activity", "languages",
                    "topics", "actions_workflows"
                ],
                "key_organizations": [
                    "ethereum", "bitcoin", "solana-labs",
                    "cosmos", "polkadot-js", "near",
                    "ava-labs", "starkware-libs",
                    "matter-labs", "scroll-tech",
                    "offchainlabs", "ethereum-optimism",
                    "paradigmxyz", "foundry-rs",
                    "Uniswap", "aave", "MakerDAO",
                    "compound-finance", "curvefi",
                    "balancer-labs", "lidofinance",
                    "eigenlayer", "celestiaorg",
                    "chainlink", "OpenZeppelin",
                    "risc0", "succinctlabs",
                    "privacy-scaling-explorations",
                ],
                "rate_limit": "5000 req/hour (authenticated)",
                "collection_method": "rest_api + graphql",
            },

            "github_archive": {
                "endpoint": "https://www.gharchive.org",
                "description": "Arquivo completo de eventos GitHub",
                "data_types": ["all_public_events"],
                "collection_method": "newline_delimited_json",
                "notes": "Para análise histórica massiva"
            },

            "npm_registry": {
                "endpoint": "https://registry.npmjs.org",
                "data_types": [
                    "package_downloads", "dependencies",
                    "versions", "maintainers"
                ],
                "key_packages": [
                    "ethers", "viem", "wagmi", "web3",
                    "@solana/web3.js", "cosmjs",
                    "@polkadot/api", "hardhat",
                    "foundry", "@openzeppelin/contracts"
                ],
                "collection_method": "rest_api",
            },

            "crates_io": {
                "endpoint": "https://crates.io/api/v1",
                "description": "Rust packages — relevante para Solana, Substrate, WASM",
                "collection_method": "rest_api",
            },

            "pkg_go_dev": {
                "endpoint": "https://pkg.go.dev",
                "description": "Go packages — relevante para Cosmos, Ethereum clients",
                "collection_method": "html_parse + api",
            },
        }
    },

    # ═══════════════════════════════════════════
    # TIER 3: SECURITY & AUDITS
    # Confiabilidade: 0.85-0.95
    # ═══════════════════════════════════════════

    "security": {
        "description": "Auditorias, vulnerabilidades, exploits",
        "reliability_score": 0.90,
        "sources": {

            "audit_databases": {
                "solodit": {
                    "url": "https://solodit.xyz",
                    "description": "Agregador de findings de auditorias",
                    "data_types": ["audit_findings", "vulnerability_patterns"],
                    "collection_method": "html_parse + api",
                },
                "code4rena": {
                    "url": "https://code4rena.com",
                    "api": "https://raw.githubusercontent.com/code-423n4/...",
                    "data_types": ["audit_contests", "findings", "severity"],
                    "collection_method": "github_api + html_parse",
                },
                "sherlock": {
                    "url": "https://audits.sherlock.xyz",
                    "data_types": ["audit_contests", "findings"],
                    "collection_method": "html_parse + api",
                },
                "cantina": {
                    "url": "https://cantina.xyz",
                    "data_types": ["audit_contests", "findings"],
                },
                "immunefi": {
                    "url": "https://immunefi.com",
                    "api": "https://api.immunefi.com",
                    "data_types": [
                        "bug_bounties", "bounty_amounts",
                        "vulnerability_reports", "payouts"
                    ],
                },
            },

            "exploit_trackers": {
                "rekt_news": {
                    "url": "https://rekt.news",
                    "data_types": ["exploit_postmortems", "loss_amounts"],
                    "collection_method": "rss + html_parse",
                },
                "defillama_hacks": {
                    "endpoint": "https://api.llama.fi/hacks",
                    "data_types": ["hack_events", "amounts", "categories"],
                },
                "slowmist_hacked": {
                    "url": "https://hacked.slowmist.io",
                    "data_types": ["hack_database"],
                },
                "chainsec_exploits": {
                    "github": "https://github.com/chainsecurity/...",
                },
            },

            "formal_verification": {
                "certora": {"url": "https://www.certora.com/reports"},
                "runtime_verification": {"url": "https://runtimeverification.com/publications"},
            },

            "smart_contract_analysis": {
                "etherscan_verified": {
                    "endpoint": "https://api.etherscan.io/api",
                    "data_types": ["verified_source_code", "abi", "proxy_impl"],
                },
                "sourcify": {
                    "endpoint": "https://sourcify.dev",
                    "data_types": ["verified_contracts", "metadata"],
                },
            },
        }
    },

    # ═══════════════════════════════════════════
    # TIER 3.5: RESEARCH & KNOWLEDGE
    # Confiabilidade: 0.80-0.95 (varia muito)
    # ═══════════════════════════════════════════

    "research_knowledge": {
        "description": "Papers, whitepapers, documentação técnica",
        "reliability_score": 0.85,
        "sources": {

            "academic": {
                "arxiv": {
                    "endpoint": "http://export.arxiv.org/api/query",
                    "categories": ["cs.CR", "cs.DC", "cs.CE", "q-fin"],
                    "search_terms": [
                        "blockchain", "cryptocurrency", "zero knowledge",
                        "consensus mechanism", "smart contract",
                        "decentralized finance", "MEV", "AMM",
                        "rollup", "sharding", "verifiable computation"
                    ],
                    "collection_method": "atom_api",
                },
                "iacr": {
                    "url": "https://eprint.iacr.org",
                    "description": "Cryptography ePrint archive",
                    "collection_method": "rss + html_parse",
                },
                "semantic_scholar": {
                    "endpoint": "https://api.semanticscholar.org/graph/v1",
                    "collection_method": "rest_api",
                },
            },

            "protocol_documentation": {
                "strategy": "Para cada protocolo de interesse, coletar:",
                "targets": [
                    "{protocol}.xyz/docs",
                    "docs.{protocol}.org",
                    "github.com/{org}/{repo}/tree/main/docs",
                    "github.com/{org}/{repo}/wiki",
                ],
                "data_types": [
                    "whitepapers", "yellowpapers", "litepaper",
                    "technical_specs", "architecture_docs",
                    "api_references", "developer_guides",
                    "economic_papers", "risk_frameworks"
                ],
                "collection_method": "targeted_crawl",
            },

            "ethereum_research": {
                "ethresear_ch": {
                    "url": "https://ethresear.ch",
                    "data_types": [
                        "research_proposals", "EIPs_discussion",
                        "protocol_research", "cryptography",
                        "economics", "scaling"
                    ],
                    "collection_method": "discourse_api",
                },
                "eips": {
                    "github": "https://github.com/ethereum/EIPs",
                    "api": "https://eips.ethereum.org",
                    "data_types": ["eip_proposals", "status", "discussions"],
                },
                "ethereum_magicians": {
                    "url": "https://ethereum-magicians.org",
                    "collection_method": "discourse_api",
                },
            },

            "industry_research": {
                "a16z_crypto": "https://a16zcrypto.com/research",
                "paradigm_research": "https://www.paradigm.xyz/writing",
                "flashbots_research": "https://writings.flashbots.net",
                "jump_crypto": "https://jumpcrypto.com/writing",
                "delphi_digital": "https://members.delphidigital.io",
                "galaxy_research": "https://www.galaxy.com/research",
                "binance_research": "https://research.binance.com",
                "coinbase_research": "https://www.coinbase.com/institutional/research-insights",
                "chainalysis_reports": "https://www.chainalysis.com/reports",
                "collection_method": "rss + html_parse + pdf_extraction",
            },

            "newsletters_blogs": {
                "vitalik_blog": "https://vitalik.eth.limo",
                "tim_roughgarden": "https://timroughgarden.org",
                "barnabe_monnot": "https://barnabe.substack.com",  # Robust Incentives Group
                "mike_neuder": "https://mirror.xyz/mikeneuder.eth",
                "jon_charbonneau": "https://joncharbonneau.substack.com",
                "polynya": "https://polynya.mirror.xyz",
                "hasu": "https://uncommoncore.co",
                "collection_method": "rss + atom + mirror_api",
            },
        }
    },

    # ═══════════════════════════════════════════
    # TIER 4: SOCIAL & SENTIMENT
    # Confiabilidade: 0.50-0.75 (REQUER validação pesada)
    # ═══════════════════════════════════════════

    "social_sentiment": {
        "description": "Sinais sociais — úteis mas ruidosos",
        "reliability_score": 0.60,
        "sources": {

            "twitter_x": {
                "api": "https://api.twitter.com/2",
                "strategy": "Monitorar contas de alta qualidade, não trending topics",
                "high_signal_accounts": [
                    # Devs/Researchers (exemplos de categorias)
                    "CATEGORY:core_devs",
                    "CATEGORY:security_researchers",
                    "CATEGORY:protocol_founders",
                    "CATEGORY:governance_delegates",
                    "CATEGORY:mev_researchers",
                ],
                "data_types": [
                    "tweets", "threads", "engagement_metrics",
                    "follower_graphs", "list_memberships"
                ],
                "collection_method": "twitter_api_v2",
            },

            "reddit": {
                "api": "https://oauth.reddit.com",
                "subreddits": [
                    "r/ethereum", "r/ethfinance",
                    "r/CryptoCurrency", "r/bitcoin",
                    "r/solana", "r/cosmosnetwork",
                    "r/polkadot", "r/defi",
                    "r/ethdev", "r/cryptography"
                ],
                "collection_method": "reddit_api",
            },

            "discord_public": {
                "description": "Canais públicos de governança/desenvolvimento",
                "notes": "Apenas canais explicitamente públicos",
                "collection_method": "discord_api (bot authorized)",
            },

            "telegram_public": {
                "description": "Channels e grupos públicos de anúncios",
                "collection_method": "telegram_bot_api",
            },

            "farcaster": {
                "endpoint": "https://api.neynar.com/v2/farcaster",
                "description": "Protocolo social descentralizado — alta qualidade crypto-native",
                "data_types": ["casts", "channels", "reactions", "users"],
                "collection_method": "rest_api",
                "notes": "ALTO SINAL — comunidade crypto técnica"
            },

            "lens_protocol": {
                "endpoint": "https://api-v2.lens.dev/graphql",
                "description": "Social layer on-chain",
                "collection_method": "graphql",
            },
        }
    },

    # ═══════════════════════════════════════════
    # TIER 4: REGULATORY & LEGAL
    # Confiabilidade: 0.90-0.99 (fontes oficiais)
    # ═══════════════════════════════════════════

    "regulatory": {
        "description": "Dados regulatórios públicos",
        "reliability_score": 0.95,
        "sources": {
            "sec_edgar": {
                "endpoint": "https://efts.sec.gov/LATEST/search-index",
                "data_types": ["filings", "enforcement_actions"],
            },
            "cftc": {
                "url": "https://www.cftc.gov/LawRegulation",
            },
            "eu_mica": {
                "url": "https://eur-lex.europa.eu",
            },
            "fatf": {
                "url": "https://www.fatf-gafi.org/en/publications",
            },
            "bis": {
                "url": "https://www.bis.org/topic/fintech.htm",
            },
            "fed_speeches": {
                "url": "https://www.federalreserve.gov/newsevents/speeches.htm",
            },
        }
    },

    # ═══════════════════════════════════════════
    # TIER 5: MEV & ADVANCED ON-CHAIN
    # Confiabilidade: 0.85-0.95
    # ═══════════════════════════════════════════

    "mev_advanced": {
        "description": "MEV, block building, PBS",
        "reliability_score": 0.90,
        "sources": {
            "flashbots": {
                "mev_explore": "https://mev-explore.flashbots.net",
                "relay_api": "https://boost-relay.flashbots.net",
                "mev_share": "https://mev-share.flashbots.net",
                "transparency_api": "https://blocks.flashbots.net",
                "data_types": [
                    "mev_extracted", "bundle_stats",
                    "builder_stats", "relay_registrations",
                    "proposer_payments", "block_submissions"
                ],
            },
            "mev_boost_relays": {
                "ultrasound": "https://relay.ultrasound.money",
                "bloxroute": "https://bloxroute.regulated.blxrbdn.com",
                "aestus": "https://mainnet-relay.securerpc.com",
                "agnostic": "https://agnostic-relay.net",
                "data_types": [
                    "relay_bids", "winning_bids",
                    "builder_submissions", "proposer_registrations"
                ],
            },
            "eigenphi": {
                "url": "https://eigenphi.io",
                "data_types": [
                    "sandwich_attacks", "arbitrage",
                    "liquidations", "jit_liquidity"
                ],
            },
            "zeromev": {
                "url": "https://zeromev.org",
                "api": "https://api.zeromev.org",
                "data_types": ["mev_transactions", "mev_type_classification"],
            },
            "libmev": {
                "url": "https://libmev.com",
                "data_types": ["builder_profitability", "censorship_data"],
            },
            "payload_de": {
                "url": "https://payload.de",
                "data_types": ["relay_analytics", "builder_dominance"],
            },
            "inclusion_watch": {
                "url": "https://www.inclusion.watch",
                "data_types": ["censorship_resistance_metrics"],
            },
        }
    },

    # ═══════════════════════════════════════════
    # TIER 5: ZK & CRYPTOGRAPHY SPECIFIC
    # ═══════════════════════════════════════════

    "zk_cryptography": {
        "description": "Dados específicos de ZK technology",
        "reliability_score": 0.88,
        "sources": {
            "zk_benchmarks": {
                "url": "https://zkbench.dev",
                "data_types": ["prover_benchmarks", "verification_costs"],
            },
            "l2beat_zk": {
                "data_types": [
                    "zk_rollup_tech_details", "proof_systems",
                    "circuit_types", "verification_contracts"
                ],
            },
            "proof_systems_repos": {
                "plonky2": "github.com/0xPolygonZero/plonky2",
                "halo2": "github.com/zcash/halo2",
                "circom": "github.com/iden3/circom",
                "noir": "github.com/noir-lang/noir",
                "cairo": "github.com/starkware-libs/cairo",
                "sp1": "github.com/succinctlabs/sp1",
                "risc0": "github.com/risc0/risc0",
                "jolt": "github.com/a16z/jolt",
            },
            "zk_summit_recordings": {
                "url": "https://www.youtube.com/@zkSummit",
            },
        }
    },
}
