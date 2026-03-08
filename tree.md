Mano, fui fazer um projeto com o CLaude, olha isso aqui:

````bash
markdownCopy# CHAINSCOPE — COMPLETE PROJECT TREE + IMPLEMENTATION INSTRUCTIONS FOR CLAUDE CODE

## COMPLETE DIRECTORY TREE
chainscope/
│
├── README.md
├── pyproject.toml
├── Makefile
├── docker-compose.yml
├── docker-compose.dev.yml
├── docker-compose.prod.yml
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
│
├── config/
│   ├── pipeline.yml                    # Master pipeline configuration
│   ├── sources.yml                     # All data source definitions
│   ├── protocols.yml                   # Protocol universe (what to monitor)
│   ├── schedules.yml                   # Collection schedules (cron)
│   ├── validation_rules.yml            # Cross-source validation rules
│   ├── alerts.yml                      # Alert thresholds and routing
│   ├── rate_limits.yml                 # Per-domain rate limit configs
│   ├── storage.yml                     # Database connection configs
│   ├── enrichment.yml                  # LLM/GPU enrichment configs
│   ├── feature_flags.yml              # Feature toggles
│   └── secrets.yml.enc                # Encrypted API keys (sops)
│
├── infrastructure/
│   ├── docker/
│   │   ├── Dockerfile.collector       # Collector service image
│   │   ├── Dockerfile.validator       # Validator service image
│   │   ├── Dockerfile.normalizer      # Normalizer service image
│   │   ├── Dockerfile.enrichment      # Enrichment service (GPU)
│   │   ├── Dockerfile.analysis        # Analysis service image
│   │   ├── Dockerfile.api             # API service image
│   │   ├── Dockerfile.orchestrator    # Orchestrator service image
│   │   └── Dockerfile.monitoring      # Monitoring sidecar
│   │
│   ├── migrations/
│   │   ├── timescaledb/
│   │   │   ├── 001_initial_schema.sql
│   │   │   ├── 002_protocol_metrics.sql
│   │   │   ├── 003_market_data.sql
│   │   │   ├── 004_governance_data.sql
│   │   │   ├── 005_security_events.sql
│   │   │   ├── 006_developer_metrics.sql
│   │   │   ├── 007_continuous_aggregates.sql
│   │   │   ├── 008_retention_policies.sql
│   │   │   ├── 009_compression_policies.sql
│   │   │   ├── 010_data_lineage.sql
│   │   │   └── 011_indexes_and_partitions.sql
│   │   │
│   │   ├── neo4j/
│   │   │   ├── 001_constraints.cypher
│   │   │   ├── 002_indexes.cypher
│   │   │   ├── 003_initial_taxonomy.cypher
│   │   │   └── 004_graph_projections.cypher
│   │   │
│   │   ├── clickhouse/
│   │   │   ├── 001_on_chain_events.sql
│   │   │   ├── 002_market_microstructure.sql
│   │   │   ├── 003_materialized_views.sql
│   │   │   └── 004_dictionaries.sql
│   │   │
│   │   └── qdrant/
│   │       ├── 001_collections.py
│   │       └── 002_payload_indexes.py
│   │
│   ├── scripts/
│   │   ├── init_databases.sh          # Initialize all databases
│   │   ├── run_migrations.sh          # Run all migrations
│   │   ├── seed_protocol_universe.py  # Seed initial protocol data
│   │   ├── seed_source_taxonomy.py    # Seed source configurations
│   │   ├── health_check_all.sh        # Check all services
│   │   ├── backup.sh                  # Backup all databases
│   │   └── restore.sh                 # Restore from backup
│   │
│   └── monitoring/
│       ├── prometheus/
│       │   ├── prometheus.yml
│       │   ├── alerts/
│       │   │   ├── pipeline_alerts.yml
│       │   │   ├── source_alerts.yml
│       │   │   ├── storage_alerts.yml
│       │   │   └── quality_alerts.yml
│       │   └── recording_rules/
│       │       ├── collection_rules.yml
│       │       └── quality_rules.yml
│       │
│       ├── grafana/
│       │   ├── provisioning/
│       │   │   ├── datasources.yml
│       │   │   └── dashboards.yml
│       │   └── dashboards/
│       │       ├── pipeline_overview.json
│       │       ├── source_health.json
│       │       ├── data_quality.json
│       │       ├── storage_metrics.json
│       │       ├── gpu_utilization.json
│       │       └── collection_rates.json
│       │
│       └── alertmanager/
│           └── alertmanager.yml
│
├── src/
│   └── chainscope/
│       ├── init.py
│       ├── main.py                # CLI entrypoint
│       ├── version.py
│       │
│       ├── core/
│       │   ├── init.py
│       │   ├── config.py              # Configuration loader (pydantic-settings)
│       │   ├── models.py              # Core domain models (pydantic v2)
│       │   ├── enums.py               # All enumerations
│       │   ├── exceptions.py          # Custom exception hierarchy
│       │   ├── constants.py           # Global constants
│       │   ├── types.py              # Custom type aliases
│       │   ├── events.py             # Internal event system
│       │   ├── interfaces.py          # Abstract interfaces (protocols)
│       │   └── utils/
│       │       ├── init.py
│       │       ├── hashing.py         # Content hashing (SHA-256, xxhash)
│       │       ├── retry.py           # Retry with backoff decorators
│       │       ├── rate_limit.py      # Token bucket + sliding window
│       │       ├── serialization.py   # orjson + msgpack helpers
│       │       ├── compression.py     # zstandard helpers
│       │       ├── time_utils.py      # Timezone-aware datetime helpers
│       │       ├── address.py         # Blockchain address validation/checksums
│       │       ├── pagination.py      # API pagination helpers
│       │       ├── backpressure.py    # Bounded async queue with backpressure
│       │       ├── circuit_breaker.py # Circuit breaker pattern
│       │       └── bloom_filter.py    # Probabilistic dedup
│       │
│       ├── collector/
│       │   ├── init.py
│       │   ├── engine.py              # Main collection engine
│       │   │                          #   - Manages all adapters
│       │   │                          #   - Dispatches collection tasks
│       │   │                          #   - Handles backpressure from downstream
│       │   │                          #   - Emits RawDataPoint to validation queue
│       │   │
│       │   ├── scheduler.py           # Collection job scheduler
│       │   │                          #   - Cron-based scheduling
│       │   │                          #   - Priority queue management
│       │   │                          #   - Dependency resolution between jobs
│       │   │                          #   - Catch-up logic for missed runs
│       │   │
│       │   ├── task.py                # CollectionTask dataclass + factory
│       │   ├── result.py              # RawDataPoint + CollectionResult models
│       │   │
│       │   ├── rate_limiter/
│       │   │   ├── init.py
│       │   │   ├── distributed.py     # Redis-backed distributed rate limiter
│       │   │   ├── token_bucket.py    # Token bucket algorithm
│       │   │   ├── sliding_window.py  # Sliding window counter
│       │   │   ├── adaptive.py        # Adaptive rate limiting (reads HTTP headers)
│       │   │   └── robots.py          # robots.txt parser and respecter
│       │   │
│       │   ├── adapters/
│       │   │   ├── init.py
│       │   │   ├── base.py            # BaseAdapter ABC
│       │   │   │                      #   async health_check() -> bool
│       │   │   │                      #   async collect(params) -> AsyncIterator[RawDataPoint]
│       │   │   │                      #   async validate_response(data) -> bool
│       │   │   │                      #   get_rate_limit_config() -> RateLimitConfig
│       │   │   │                      #   get_schema() -> dict (JSON Schema)
│       │   │   │
│       │   │   ├── generic/
│       │   │   │   ├── init.py
│       │   │   │   ├── rest.py        # Generic REST API adapter
│       │   │   │   │                  #   - GET/POST with retry
│       │   │   │   │                  #   - Auto-pagination (cursor, offset, page)
│       │   │   │   │                  #   - Response caching
│       │   │   │   │                  #   - Rate limit header parsing
│       │   │   │   │
│       │   │   │   ├── graphql.py     # Generic GraphQL adapter
│       │   │   │   │                  #   - Query batching
│       │   │   │   │                  #   - Pagination via cursors
│       │   │   │   │                  #   - Schema introspection
│       │   │   │   │
│       │   │   │   ├── websocket.py   # Generic WebSocket adapter
│       │   │   │   │                  #   - Auto-reconnect with backoff
│       │   │   │   │                  #   - Heartbeat/ping management
│       │   │   │   │                  #   - Message buffering
│       │   │   │   │                  #   - Subscription management
│       │   │   │   │
│       │   │   │   ├── json_rpc.py    # Generic JSON-RPC 2.0 adapter
│       │   │   │   │                  #   - Batch requests
│       │   │   │   │                  #   - Provider failover
│       │   │   │   │                  #   - Response validation
│       │   │   │   │
│       │   │   │   ├── rss.py         # RSS/Atom feed parser
│       │   │   │   │                  #   - feedparser integration
│       │   │   │   │                  #   - Incremental fetch (etag/modified)
│       │   │   │   │                  #   - Content extraction from links
│       │   │   │   │
│       │   │   │   ├── discourse.py   # Discourse forum API adapter
│       │   │   │   │                  #   - Topics, posts, categories
│       │   │   │   │                  #   - User profiles
│       │   │   │   │                  #   - Incremental sync
│       │   │   │   │
│       │   │   │   ├── github.py      # GitHub API v4 (GraphQL) + v3 (REST)
│       │   │   │   │                  #   - Org/repo scanning
│       │   │   │   │                  #   - Commit/PR/Issue collection
│       │   │   │   │                  #   - Rate limit management (5000/hr)
│       │   │   │   │                  #   - Conditional requests (etag)
│       │   │   │   │
│       │   │   │   ├── pdf.py         # PDF content extractor
│       │   │   │   │                  #   - Text extraction (pdfplumber)
│       │   │   │   │                  #   - Table extraction
│       │   │   │   │                  #   - Metadata extraction
│       │   │   │   │
│       │   │   │   └── html.py        # HTML content extractor
│       │   │   │                      #   - Readability extraction
│       │   │   │                      #   - Structured data (JSON-LD, microdata)
│       │   │   │                      #   - Content cleaning
│       │   │   │
│       │   │   ├── blockchain/
│       │   │   │   ├── init.py
│       │   │   │   ├── ethereum.py    # Ethereum RPC collector
│       │   │   │   │                  #   - Blocks, transactions, receipts, logs
│       │   │   │   │                  #   - eth_call for state queries
│       │   │   │   │                  #   - Event log filtering
│       │   │   │   │                  #   - Multicall batching
│       │   │   │   │                  #   - Provider rotation/failover
│       │   │   │   │
│       │   │   │   ├── ethereum_beacon.py  # Beacon chain API
│       │   │   │   │                       #   - Validator set
│       │   │   │   │                       #   - Attestations/slots
│       │   │   │   │                       #   - SSE event stream
│       │   │   │   │
│       │   │   │   ├── solana.py      # Solana RPC collector
│       │   │   │   │                  #   - getProgramAccounts
│       │   │   │   │                  #   - getSignaturesForAddress
│       │   │   │   │                  #   - Token accounts/balances
│       │   │   │   │                  #   - Vote accounts/stake
│       │   │   │   │
│       │   │   │   ├── cosmos.py      # Cosmos LCD/RPC collector
│       │   │   │   │                  #   - Chain registry integration
│       │   │   │   │                  #   - IBC channels/connections
│       │   │   │   │                  #   - Governance proposals
│       │   │   │   │                  #   - Validator sets
│       │   │   │   │
│       │   │   │   ├── substrate.py   # Polkadot/Substrate collector
│       │   │   │   │                  #   - Parachains
│       │   │   │   │                  #   - XCM messages
│       │   │   │   │                  #   - Staking/nominations
│       │   │   │   │
│       │   │   │   ├── bitcoin.py     # Bitcoin REST API collector
│       │   │   │   │                  #   - Blocks, transactions
│       │   │   │   │                  #   - Mempool stats
│       │   │   │   │                  #   - Fee estimates
│       │   │   │   │
│       │   │   │   ├── evm_generic.py # Generic EVM chain collector
│       │   │   │   │                  #   - Works for any EVM L2
│       │   │   │   │                  #   - Chain-specific overrides
│       │   │   │   │
│       │   │   │   ├── starknet.py    # StarkNet specific
│       │   │   │   └── near.py        # NEAR specific
│       │   │   │
│       │   │   ├── aggregators/
│       │   │   │   ├── init.py
│       │   │   │   ├── defillama.py   # DefiLlama full API coverage
│       │   │   │   │                  #   - Protocols, TVL, volumes
│       │   │   │   │                  #   - Yields, stablecoins, bridges
│       │   │   │   │                  #   - Fees, revenue, raises
│       │   │   │   │                  #   - Hacks, treasuries, emissions
│       │   │   │   │                  #   - Coin prices (current + historical)
│       │   │   │   │
│       │   │   │   ├── coingecko.py   # CoinGecko API
│       │   │   │   │                  #   - Market data, OHLC
│       │   │   │   │                  #   - Categories, trending
│       │   │   │   │                  #   - Exchange data
│       │   │   │   │
│       │   │   │   ├── coinmarketcap.py # CMC API
│       │   │   │   ├── l2beat.py      # L2Beat API + GitHub data
│       │   │   │   │                  #   - TVL, risk analysis
│       │   │   │   │                  #   - Technology details
│       │   │   │   │                  #   - Stage classification
│       │   │   │   │
│       │   │   │   ├── token_terminal.py  # Token Terminal
│       │   │   │   ├── messari.py     # Messari API
│       │   │   │   ├── dune.py        # Dune Analytics API
│       │   │   │   │                  #   - Execute queries
│       │   │   │   │                  #   - Poll for results
│       │   │   │   │                  #   - Query library management
│       │   │   │   │
│       │   │   │   ├── flipside.py    # Flipside Crypto API
│       │   │   │   └── electric_capital.py  # Dev ecosystem mapping
│       │   │   │
│       │   │   ├── market/
│       │   │   │   ├── init.py
│       │   │   │   ├── ccxt_unified.py    # CCXT exchange adapter
│       │   │   │   │                      #   - Unified orderbook, trades, OHLCV
│       │   │   │   │                      #   - Funding rates, OI
│       │   │   │   │                      #   - WebSocket streams
│       │   │   │   │                      #   - Exchange health monitoring
│       │   │   │   │
│       │   │   │   ├── coinalyze.py       # Derivatives data
│       │   │   │   ├── laevitas.py        # Options analytics
│       │   │   │   ├── kaiko.py           # Institutional market data
│       │   │   │   └── dex_aggregators.py # 0x, 1inch, Jupiter, CoW
│       │   │   │
│       │   │   ├── governance/
│       │   │   │   ├── init.py
│       │   │   │   ├── snapshot.py    # Snapshot.org GraphQL
│       │   │   │   ├── tally.py       # Tally on-chain governance
│       │   │   │   ├── boardroom.py   # Boardroom API
│       │   │   │   ├── agora.py       # Agora governance
│       │   │   │   └── forums.py      # Discourse forum scanner
│       │   │   │                      #   - MakerDAO, Aave, Arbitrum, etc.
│       │   │   │                      #   - Template for any Discourse instance
│       │   │   │
│       │   │   ├── security/
│       │   │   │   ├── init.py
│       │   │   │   ├── solodit.py     # Audit findings aggregator
│       │   │   │   ├── code4rena.py   # Code4rena contests/findings
│       │   │   │   ├── sherlock.py    # Sherlock audits
│       │   │   │   ├── immunefi.py    # Bug bounties
│       │   │   │   ├── rekt.py        # Rekt.news exploit tracker
│       │   │   │   ├── etherscan_contracts.py  # Verified contract source
│       │   │   │   ├── sourcify.py    # Sourcify verified contracts
│       │   │   │   └── chainalysis_sanctions.py  # OFAC/sanctions lists
│       │   │   │
│       │   │   ├── research/
│       │   │   │   ├── init.py
│       │   │   │   ├── arxiv.py       # arXiv paper collector
│       │   │   │   ├── iacr.py        # IACR ePrint collector
│       │   │   │   ├── semantic_scholar.py  # Academic paper search
│       │   │   │   ├── mirror.py      # Mirror.xyz blog posts
│       │   │   │   ├── substack.py    # Substack newsletters
│       │   │   │   ├── medium.py      # Medium blog posts
│       │   │   │   ├── protocol_docs.py    # Protocol documentation crawler
│       │   │   │   │                       #   - Gitbook, Docusaurus, etc.
│       │   │   │   │                       #   - Whitepaper PDF extraction
│       │   │   │   │
│       │   │   │   ├── ethresearch.py      # ethresear.ch (Discourse)
│       │   │   │   ├── eips.py             # EIP tracker (GitHub)
│       │   │   │   └── industry_blogs.py   # a16z, Paradigm, Flashbots, etc.
│       │   │   │
│       │   │   ├── mev/
│       │   │   │   ├── init.py
│       │   │   │   ├── flashbots.py       # Flashbots transparency data
│       │   │   │   ├── mev_boost_relays.py # All relay APIs
│       │   │   │   ├── eigenphi.py        # MEV type classification
│       │   │   │   ├── zeromev.py         # MEV transaction data
│       │   │   │   ├── libmev.py          # Builder profitability
│       │   │   │   ├── payload_de.py      # Relay analytics
│       │   │   │   └── inclusion_watch.py # Censorship metrics
│       │   │   │
│       │   │   ├── social/
│       │   │   │   ├── init.py
│       │   │   │   ├── farcaster.py   # Farcaster via Neynar API
│       │   │   │   ├── lens.py        # Lens Protocol GraphQL
│       │   │   │   ├── reddit.py      # Reddit API
│       │   │   │   ├── twitter.py     # Twitter/X API v2
│       │   │   │   └── telegram.py    # Telegram public channels
│       │   │   │
│       │   │   ├── regulatory/
│       │   │   │   ├── init.py
│       │   │   │   ├── sec_edgar.py   # SEC filings
│       │   │   │   ├── cftc.py        # CFTC actions
│       │   │   │   ├── eu_mica.py     # EU MiCA tracker
│       │   │   │   ├── fatf.py        # FATF publications
│       │   │   │   └── fed.py         # Fed speeches on crypto
│       │   │   │
│       │   │   ├── developer/
│       │   │   │   ├── init.py
│       │   │   │   ├── github_deep.py     # Deep GitHub scanner
│       │   │   │   │                      #   - Org-level scanning
│       │   │   │   │                      #   - Contributor analysis
│       │   │   │   │                      #   - Dependency extraction
│       │   │   │   │                      #   - Code frequency analysis
│       │   │   │   │
│       │   │   │   ├── github_archive.py  # GH Archive historical
│       │   │   │   ├── npm.py             # npm registry stats
│       │   │   │   ├── crates_io.py       # Rust crates stats
│       │   │   │   └── pypi.py            # Python package stats
│       │   │   │
│       │   │   └── indexers/
│       │   │       ├── init.py
│       │   │       ├── the_graph.py       # The Graph subgraphs
│       │   │       ├── subsquid.py        # Subsquid indexer
│       │   │       ├── goldsky.py         # Goldsky subgraphs
│       │   │       ├── nansen.py          # Nansen labels/analytics
│       │   │       └── arkham.py          # Arkham Intelligence
│       │   │
│       │   └── _registry.py          # Adapter registry
│       │                              #   - Auto-discovery of adapters
│       │                              #   - Factory pattern for instantiation
│       │                              #   - Health check aggregation
│       │
│       ├── validator/
│       │   ├── init.py
│       │   ├── pipeline.py            # Validation pipeline orchestrator
│       │   │                          #   - Runs all validation stages in order
│       │   │                          #   - Aggregates results into ValidationResult
│       │   │                          #   - Routes failed validations
│       │   │
│       │   ├── result.py              # ValidationResult model
│       │   │
│       │   ├── stages/
│       │   │   ├── init.py
│       │   │   ├── structural.py      # Stage 1: JSON Schema compliance
│       │   │   │                      #   - Required fields present
│       │   │   │                      #   - Data types correct
│       │   │   │                      #   - Format validation (addresses, URLs)
│       │   │   │
│       │   │   ├── temporal.py        # Stage 2: Time-based validation
│       │   │   │                      #   - Not in future
│       │   │   │                      #   - Not too stale
│       │   │   │                      #   - Ordering consistency
│       │   │   │                      #   - Gap detection in timeseries
│       │   │   │
│       │   │   ├── semantic.py        # Stage 3: Domain-specific rules
│       │   │   │                      #   - TVL >= 0
│       │   │   │                      #   - market_cap = price * supply
│       │   │   │                      #   - Valid chain_id
│       │   │   │                      #   - Valid address checksum
│       │   │   │
│       │   │   ├── statistical.py     # Stage 4: Anomaly-based validation
│       │   │   │                      #   - Z-score against rolling window
│       │   │   │                      #   - IQR outlier detection
│       │   │   │                      #   - Percentage change threshold
│       │   │   │
│       │   │   ├── cross_source.py    # Stage 5: Cross-reference validation
│       │   │   │                      #   - Compare prices across sources
│       │   │   │                      #   - Compare TVL across sources
│       │   │   │                      #   - Flag discrepancies
│       │   │   │                      #   - Median consensus strategy
│       │   │   │
│       │   │   └── freshness.py       # Stage 6: Freshness check
│       │   │                          #   - Is data newer than stored?
│       │   │                          #   - Is source data fresh?
│       │   │
│       │   └── rules/
│       │       ├── init.py
│       │       ├── price_rules.py     # Price-specific validation rules
│       │       ├── tvl_rules.py       # TVL-specific validation rules
│       │       ├── supply_rules.py    # Supply-specific validation rules
│       │       ├── governance_rules.py # Governance data rules
│       │       └── chain_rules.py     # Chain-specific rules (known chain_ids, etc.)
│       │
│       ├── normalizer/
│       │   ├── init.py
│       │   ├── engine.py              # Normalization engine
│       │   │                          #   - Routes raw data to appropriate mapper
│       │   │                          #   - Applies schema transformation
│       │   │                          #   - Handles version migration
│       │   │
│       │   ├── deduplicator.py        # Deduplication engine
│       │   │                          #   - Content hash dedup
│       │   │                          #   - Semantic dedup (near-duplicate detection)
│       │   │                          #   - Bloom filter for fast checks
│       │   │                          #   - Redis-backed for distributed dedup
│       │   │
│       │   ├── schemas/
│       │   │   ├── init.py
│       │   │   ├── base.py            # Base normalized schema
│       │   │   ├── protocol.py        # Protocol entity schema (Pydantic v2)
│       │   │   ├── chain.py           # Chain entity schema
│       │   │   ├── token.py           # Token entity schema
│       │   │   ├── market_data.py     # Market data point schema
│       │   │   ├── governance.py      # Governance proposal/vote schema
│       │   │   ├── security.py        # Audit/vulnerability schema
│       │   │   ├── developer.py       # Developer activity schema
│       │   │   ├── research.py        # Research document schema
│       │   │   ├── mev.py             # MEV event schema
│       │   │   ├── social.py          # Social signal schema
│       │   │   └── regulatory.py      # Regulatory event schema
│       │   │
│       │   └── mappers/
│       │       ├── init.py
│       │       ├── base.py            # BaseMapper ABC
│       │       │                      #   map(raw: RawDataPoint) -> NormalizedEntity
│       │       │
│       │       ├── defillama_mapper.py     # DefiLlama -> Protocol/Token/Market
│       │       ├── coingecko_mapper.py     # CoinGecko -> Token/Market
│       │       ├── l2beat_mapper.py        # L2Beat -> Chain/Protocol
│       │       ├── github_mapper.py        # GitHub -> Developer activity
│       │       ├── snapshot_mapper.py      # Snapshot -> Governance
│       │       ├── ccxt_mapper.py          # CCXT -> Market data
│       │       ├── etherscan_mapper.py     # Etherscan -> Contract/Chain
│       │       ├── flashbots_mapper.py     # Flashbots -> MEV
│       │       ├── rpc_mapper.py           # RPC responses -> Chain metrics
│       │       ├── arxiv_mapper.py         # arXiv -> Research
│       │       ├── audit_mapper.py         # Audit reports -> Security
│       │       └── forum_mapper.py         # Forum posts -> Governance/Social
│       │
│       ├── enrichment/
│       │   ├── init.py
│       │   ├── pipeline.py            # Enrichment pipeline orchestrator
│       │   │                          #   - Routes data to appropriate enrichers
│       │   │                          #   - Manages GPU resource allocation
│       │   │                          #   - Batches requests for efficiency
│       │   │
│       │   ├── embeddings/
│       │   │   ├── init.py
│       │   │   ├── generator.py       # Embedding generation engine
│       │   │   │                      #   - Sentence transformers
│       │   │   │                      #   - Chunking strategy (recursive text splitter)
│       │   │   │                      #   - Batch processing on GPU
│       │   │   │                      #   - Cache to avoid recomputation
│       │   │   │
│       │   │   ├── chunker.py         # Document chunking strategies
│       │   │   │                      #   - Recursive character splitter
│       │   │   │                      #   - Semantic chunking
│       │   │   │                      #   - Code-aware chunking
│       │   │   │
│       │   │   └── models.py          # Embedding model management
│       │   │                          #   - Model loading/caching
│       │   │                          #   - Batch inference
│       │   │
│       │   ├── nlp/
│       │   │   ├── init.py
│       │   │   ├── ner.py             # Named Entity Recognition
│       │   │   │                      #   - Protocol names
│       │   │   │                      #   - Person names
│       │   │   │                      #   - Technology terms
│       │   │   │                      #   - Token symbols
│       │   │   │                      #   - Chain names
│       │   │   │
│       │   │   ├── summarizer.py      # Document summarization
│       │   │   │                      #   - Whitepaper summaries
│       │   │   │                      #   - Audit report summaries
│       │   │   │                      #   - Research paper abstracts
│       │   │   │                      #   - Forum thread summaries
│       │   │   │
│       │   │   ├── classifier.py      # Multi-label classification
│       │   │   │                      #   - Technology classification
│       │   │   │                      #   - Topic classification
│       │   │   │                      #   - Sentiment classification
│       │   │   │                      #   - Risk classification
│       │   │   │
│       │   │   ├── sentiment.py       # Crypto-calibrated sentiment
│       │   │   │                      #   - Bullish/bearish/neutral
│       │   │   │                      #   - Technical optimism/pessimism
│       │   │   │                      #   - FUD vs legitimate concern
│       │   │   │
│       │   │   └── relationship.py    # Relationship extraction
│       │   │                          #   - "uses", "competes_with", "depends_on"
│       │   │                          #   - "founded_by", "audited_by"
│       │   │                          #   - "forked_from", "bridges_to"
│       │   │
│       │   ├── scoring/
│       │   │   ├── init.py
│       │   │   ├── risk_scorer.py     # Protocol risk scoring
│       │   │   │                      #   - Smart contract risk
│       │   │   │                      #   - Centralization risk
│       │   │   │                      #   - Oracle dependency risk
│       │   │   │                      #   - Liquidity risk
│       │   │   │                      #   - Governance risk
│       │   │   │                      #   - Composite risk score
│       │   │   │
│       │   │   ├── health_scorer.py   # Protocol health scoring
│       │   │   │                      #   - Financial health
│       │   │   │                      #   - Technical health
│       │   │   │                      #   - Community health
│       │   │   │                      #   - Security health
│       │   │   │
│       │   │   └── quality_scorer.py  # Data quality scoring
│       │   │                          #   - Completeness
│       │   │                          #   - Freshness
│       │   │                          #   - Consistency
│       │   │                          #   - Accuracy confidence
│       │   │
│       │   └── graph/
│       │       ├── init.py
│       │       └── relationship_builder.py  # Build graph edges from enrichments
│       │                                    #   - Entity resolution
│       │                                    #   - Relationship typing
│       │                                    #   - Confidence scoring
│       │
│       ├── storage/
│       │   ├── init.py
│       │   ├── manager.py             # Storage manager (routes to correct store)
│       │   │                          #   - Determines which store(s) for each data type
│       │   │                          #   - Handles write fanout (one input -> multiple stores)
│       │   │                          #   - Transaction management
│       │   │
│       │   ├── timescale/
│       │   │   ├── init.py
│       │   │   ├── client.py          # AsyncPG client wrapper
│       │   │   │                      #   - Connection pooling
│       │   │   │                      #   - Bulk upsert (COPY protocol)
│       │   │   │                      #   - Prepared statements
│       │   │   │                      #   - Health checks
│       │   │   │
│       │   │   ├── models.py          # SQLAlchemy / raw SQL models
│       │   │   ├── queries.py         # Pre-built analytical queries
│       │   │   └── maintenance.py     # Compression, retention, reorder
│       │   │
│       │   ├── neo4j/
│       │   │   ├── init.py
│       │   │   ├── client.py          # Neo4j async driver wrapper
│       │   │   │                      #   - Connection management
│       │   │   │                      #   - Batch MERGE operations
│       │   │   │                      #   - Transaction functions
│       │   │   │
│       │   │   ├── queries.py         # Pre-built Cypher queries
│       │   │   │                      #   - Dependency traversal
│       │   │   │                      #   - Path finding
│       │   │   │                      #   - Community detection
│       │   │   │                      #   - Centrality metrics
│       │   │   │
│       │   │   └── projections.py     # Graph Data Science projections
│       │   │
│       │   ├── qdrant/
│       │   │   ├── init.py
│       │   │   ├── client.py          # Qdrant client wrapper
│       │   │   │                      #   - Collection management
│       │   │   │                      #   - Batch upsert
│       │   │   │                      #   - Filtered search
│       │   │   │                      #   - Scroll API for export
│       │   │   │
│       │   │   └── search.py          # Search helpers
│       │   │                          #   - Semantic search
│       │   │                          #   - Hybrid search (vector + filter)
│       │   │                          #   - Multi-collection search
│       │   │                          #   - Recommendation engine
│       │   │
│       │   ├── clickhouse/
│       │   │   ├── init.py
│       │   │   ├── client.py          # ClickHouse client wrapper
│       │   │   │                      #   - Async inserts
│       │   │   │                      #   - Batch buffering
│       │   │   │                      #   - Query execution
│       │   │   │
│       │   │   └── queries.py         # Pre-built analytical queries
│       │   │                          #   - Cross-protocol comparisons
│       │   │                          #   - Historical aggregations
│       │   │                          #   - Funnel analysis
│       │   │
│       │   ├── redis/
│       │   │   ├── init.py
│       │   │   ├── client.py          # Redis async client wrapper
│       │   │   ├── cache.py           # Caching layer
│       │   │   │                      #   - TTL-based cache
│       │   │   │                      #   - Cache invalidation
│       │   │   │                      #   - Cache warming
│       │   │   │
│       │   │   ├── queue.py           # Job queue (Redis Streams)
│       │   │   │                      #   - Priority queues
│       │   │   │                      #   - Consumer groups
│       │   │   │                      #   - Dead letter queue
│       │   │   │
│       │   │   ├── pubsub.py          # Pub/Sub for real-time events
│       │   │   └── locks.py           # Distributed locks (Redlock)
│       │   │
│       │   ├── object_store/
│       │   │   ├── init.py
│       │   │   ├── client.py          # MinIO/S3 client wrapper
│       │   │   │                      #   - Streaming upload/download
│       │   │   │                      #   - Compression on write
│       │   │   │                      #   - Lifecycle policies
│       │   │   │
│       │   │   └── paths.py           # Path generation helpers
│       │   │
│       │   └── lineage/
│       │       ├── init.py
│       │       ├── tracker.py         # Data lineage tracker
│       │       │                      #   - Record every transformation
│       │       │                      #   - Link to raw source
│       │       │                      #   - Track cross-validation
│       │       │                      #   - Audit trail
│       │       │
│       │       └── models.py          # Lineage data models
│       │
│       ├── analysis/
│       │   ├── init.py
│       │   ├── engine.py              # Analysis engine orchestrator
│       │   │                          #   - Schedules analytical queries
│       │   │                          #   - Manages compute resources
│       │   │                          #   - Caches results
│       │   │
│       │   ├── anomaly/
│       │   │   ├── init.py
│       │   │   ├── detector.py        # Anomaly detection engine
│       │   │   │                      #   - Z-score detector
│       │   │   │                      #   - IQR detector
│       │   │   │                      #   - Percentage change detector
│       │   │   │                      #   - Cross-source divergence
│       │   │   │
│       │   │   ├── price_anomaly.py   # Price-specific anomaly detection
│       │   │   ├── tvl_anomaly.py     # TVL-specific anomaly detection
│       │   │   ├── governance_anomaly.py   # Governance anomalies
│       │   │   ├── developer_anomaly.py    # Dev activity anomalies
│       │   │   ├── security_anomaly.py     # Security early warning
│       │   │   └── on_chain_anomaly.py     # On-chain anomalies
│       │   │
│       │   ├── correlation/
│       │   │   ├── init.py
│       │   │   ├── engine.py          # Correlation engine
│       │   │   ├── tvl_flows.py       # TVL flow analysis
│       │   │   ├── dev_migration.py   # Developer migration patterns
│       │   │   ├── governance_correlation.py  # Cross-DAO voting patterns
│       │   │   ├── security_patterns.py       # Vulnerability pattern analysis
│       │   │   └── market_correlation.py      # Market structure correlations
│       │   │
│       │   ├── scoring/
│       │   │   ├── init.py
│       │   │   ├── protocol_scorecard.py   # Holistic protocol scorecard
│       │   │   ├── chain_scorecard.py      # Chain comparison scorecard
│       │   │   └── ecosystem_scorecard.py  # Ecosystem health scorecard
│       │   │
│       │   ├── risk/
│       │   │   ├── init.py
│       │   │   ├── cascade.py         # Dependency risk cascade analysis
│       │   │   │                      #   - Oracle failure scenarios
│       │   │   │                      #   - Bridge exploit blast radius
│       │   │   │                      #   - Stablecoin depeg cascades
│       │   │   │                      #   - Validator concentration risk
│       │   │   │
│       │   │   ├── scenarios.py       # Scenario modeling
│       │   │   └── systemic.py        # Systemic risk indicators
│       │   │
│       │   ├── queries/
│       │   │   ├── init.py
│       │   │   ├── library.py         # Query library registry
│       │   │   ├── protocol_queries.py     # Protocol-level queries
│       │   │   ├── market_queries.py       # Market queries
│       │   │   ├── governance_queries.py   # Governance queries
│       │   │   ├── mev_queries.py          # MEV queries
│       │   │   ├── stablecoin_queries.py   # Stablecoin queries
│       │   │   ├── l2_queries.py           # L2 comparison queries
│       │   │   └── zk_queries.py           # ZK technology queries
│       │   │
│       │   └── graph/
│       │       ├── init.py
│       │       ├── analytics.py       # Graph analytics
│       │       │                      #   - PageRank (protocol importance)
│       │       │                      #   - Community detection
│       │       │                      #   - Betweenness centrality
│       │       │                      #   - Shortest path (dependency chains)
│       │       │
│       │       └── traversal.py       # Graph traversal utilities
│       │                              #   - Blast radius computation
│       │                              #   - Dependency tree extraction
│       │                              #   - Cycle detection
│       │
│       ├── delivery/
│       │   ├── init.py
│       │   │
│       │   ├── api/
│       │   │   ├── init.py
│       │   │   ├── app.py             # FastAPI application factory
│       │   │   │                      #   - CORS configuration
│       │   │   │                      #   - Exception handlers
│       │   │   │                      #   - Lifespan management
│       │   │   │                      #   - OpenAPI customization
│       │   │   │
│       │   │   ├── dependencies.py    # FastAPI dependency injection
│       │   │   │                      #   - Database sessions
│       │   │   │                      #   - Cache clients
│       │   │   │                      #   - Auth context
│       │   │   │
│       │   │   ├── middleware/
│       │   │   │   ├── init.py
│       │   │   │   ├── auth.py        # API key authentication
│       │   │   │   ├── rate_limit.py  # API rate limiting
│       │   │   │   ├── cache.py       # Response caching (Redis)
│       │   │   │   ├── logging.py     # Request/response logging
│       │   │   │   └── compression.py # Response compression
│       │   │   │
│       │   │   ├── routes/
│       │   │   │   ├── init.py
│       │   │   │   ├── protocols.py   # /protocols/* endpoints
│       │   │   │   │                  #   GET /protocols
│       │   │   │   │                  #   GET /protocols/{id}
│       │   │   │   │                  #   GET /protocols/{id}/metrics
│       │   │   │   │                  #   GET /protocols/{id}/health
│       │   │   │   │                  #   GET /protocols/{id}/risks
│       │   │   │   │                  #   GET /protocols/{id}/graph
│       │   │   │   │                  #   GET /protocols/{id}/similar
│       │   │   │   │                  #   GET /protocols/{id}/timeline
│       │   │   │   │                  #   GET /protocols/compare
│       │   │   │   │
│       │   │   │   ├── chains.py      # /chains/* endpoints
│       │   │   │   ├── market.py      # /market/* endpoints
│       │   │   │   ├── governance.py  # /governance/* endpoints
│       │   │   │   ├── security.py    # /security/* endpoints
│       │   │   │   ├── developers.py  # /developers/* endpoints
│       │   │   │   ├── research.py    # /research/* endpoints
│       │   │   │   │                  #   GET /research/search (semantic)
│       │   │   │   │                  #   POST /research/query (NL query)
│       │   │   │   │
│       │   │   │   ├── mev.py         # /mev/* endpoints
│       │   │   │   ├── alerts.py      # /alerts/* endpoints
│       │   │   │   ├── intelligence.py # /intelligence/* endpoints
│       │   │   │   │                   #   GET /intelligence/daily-brief
│       │   │   │   │                   #   GET /intelligence/weekly-report
│       │   │   │   │                   #   POST /intelligence/custom-query
│       │   │   │   │
│       │   │   │   └── meta.py        # /meta/* endpoints
│       │   │   │                      #   GET /meta/sources (health)
│       │   │   │                      #   GET /meta/quality
│       │   │   │                      #   GET /meta/coverage
│       │   │   │                      #   GET /meta/lineage/{id}
│       │   │   │
│       │   │   └── models/
│       │   │       ├── init.py
│       │   │       ├── requests.py    # Request models (Pydantic)
│       │   │       └── responses.py   # Response models (Pydantic)
│       │   │
│       │   ├── intelligence/
│       │   │   ├── init.py
│       │   │   ├── generator.py       # Intelligence product generator
│       │   │   │                      #   - Uses LLM on B300 for synthesis
│       │   │   │                      #   - Structured output generation
│       │   │   │                      #   - Template-based reports
│       │   │   │
│       │   │   ├── daily_brief.py     # Daily intelligence brief
│       │   │   │                      #   - Market overview
│       │   │   │                      #   - Notable events
│       │   │   │                      #   - Governance digest
│       │   │   │                      #   - Security alerts
│       │   │   │                      #   - Dev highlights
│       │   │   │                      #   - Research spotlight
│       │   │   │                      #   - Risk dashboard
│       │   │   │
│       │   │   ├── weekly_report.py   # Weekly deep report
│       │   │   ├── protocol_deep_dive.py  # On-demand protocol analysis
│       │   │   ├── ecosystem_map.py   # Ecosystem visualization data
│       │   │   ├── risk_radar.py      # Risk radar dashboard data
│       │   │   ├── alpha_signals.py   # Pattern-based signal generation
│       │   │   │
│       │   │   └── templates/
│       │   │       ├── daily_brief.md.jinja2
│       │   │       ├── weekly_report.md.jinja2
│       │   │       ├── protocol_deep_dive.md.jinja2
│       │   │       ├── risk_alert.md.jinja2
│       │   │       └── anomaly_report.md.jinja2
│       │   │
│       │   ├── alerts/
│       │   │   ├── init.py
│       │   │   ├── engine.py          # Alert engine
│       │   │   │                      #   - Rule evaluation
│       │   │   │                      #   - Deduplication
│       │   │   │                      #   - Severity classification
│       │   │   │                      #   - Cooldown management
│       │   │   │
│       │   │   ├── rules.py           # Alert rule definitions
│       │   │   ├── channels/
│       │   │   │   ├── init.py
│       │   │   │   ├── webhook.py     # Webhook delivery
│       │   │   │   ├── email.py       # Email delivery
│       │   │   │   ├── slack.py       # Slack delivery
│       │   │   │   ├── telegram_out.py # Telegram delivery
│       │   │   │   └── file.py        # File-based (for testing)
│       │   │   │
│       │   │   └── formatters.py      # Alert message formatters
│       │   │
│       │   └── exports/
│       │       ├── init.py
│       │       ├── csv.py             # CSV export
│       │       ├── parquet.py         # Parquet export
│       │       ├── json_export.py     # JSON export
│       │       └── graphml.py         # GraphML export (for graph data)
│       │
│       ├── orchestrator/
│       │   ├── init.py
│       │   ├── engine.py              # Main orchestrator
│       │   │                          #   - DAG execution engine
│       │   │                          #   - Stage dependency management
│       │   │                          #   - Parallel execution control
│       │   │                          #   - Error handling & recovery
│       │   │                          #   - Pipeline state management
│       │   │
│       │   ├── dag.py                 # DAG definition & resolution
│       │   │                          #   - collect -> validate -> normalize
│       │   │                          #     -> store -> enrich -> analyze -> deliver
│       │   │                          #   - Topological sort
│       │   │                          #   - Parallel stage detection
│       │   │
│       │   ├── scheduler.py           # Master scheduler
│       │   │                          #   - Cron-based triggers
│       │   │                          #   - Event-based triggers
│       │   │                          #   - Manual triggers
│       │   │                          #   - Catch-up logic
│       │   │
│       │   ├── state.py               # Pipeline state management
│       │   │                          #   - Redis-backed state
│       │   │                          #   - Checkpointing
│       │   │                          #   - Recovery from failure
│       │   │
│       │   ├── backpressure.py        # Backpressure controller
│       │   │                          #   - Monitor queue depths
│       │   │                          #   - Throttle upstream stages
│       │   │                          #   - Adaptive concurrency
│       │   │
│       │   └── health.py             # Pipeline health aggregator
│       │                              #   - Stage health
│       │                              #   - Source health
│       │                              #   - Storage health
│       │                              #   - GPU health
│       │
│       ├── monitoring/
│       │   ├── init.py
│       │   ├── metrics.py             # Prometheus metrics definitions
│       │   │                          #   - collection_requests_total
│       │   │                          #   - collection_duration_seconds
│       │   │                          #   - validation_pass_rate
│       │   │                          #   - storage_write_duration
│       │   │                          #   - enrichment_gpu_utilization
│       │   │                          #   - queue_depth_gauge
│       │   │                          #   - data_freshness_seconds
│       │   │                          #   - source_health_gauge
│       │   │
│       │   ├── logging.py             # Structured logging setup (structlog)
│       │   │                          #   - JSON output
│       │   │                          #   - Trace ID propagation
│       │   │                          #   - Contextual binding
│       │   │
│       │   ├── tracing.py             # OpenTelemetry setup
│       │   │                          #   - Span creation helpers
│       │   │                          #   - Context propagation
│       │   │                          #   - Exporter configuration
│       │   │
│       │   └── health_checks.py       # Liveness/readiness probes
│       │                              #   - Database connectivity
│       │                              #   - GPU availability
│       │                              #   - Queue depth thresholds
│       │                              #   - Memory usage
│       │
│       └── cli/
│           ├── init.py
│           ├── main.py                # CLI entrypoint (typer/click)
│           │                          #   chainscope collect --source defillama
│           │                          #   chainscope validate --check-all
│           │                          #   chainscope analyze --query protocol_health
│           │                          #   chainscope report --type daily_brief
│           │                          #   chainscope pipeline --run full
│           │                          #   chainscope pipeline --status
│           │                          #   chainscope sources --health
│           │                          #   chainscope db --migrate
│           │                          #   chainscope db --seed
│           │                          #   chainscope export --format parquet
│           │
│           ├── commands/
│           │   ├── init.py
│           │   ├── collect.py         # Manual collection commands
│           │   ├── validate.py        # Validation commands
│           │   ├── analyze.py         # Analysis commands
│           │   ├── report.py          # Report generation commands
│           │   ├── pipeline.py        # Pipeline management commands
│           │   ├── sources.py         # Source management commands
│           │   ├── db.py              # Database management commands
│           │   └── export.py          # Data export commands
│           │
│           └── formatters.py          # CLI output formatters (rich)
│
├── tests/
│   ├── init.py
│   ├── conftest.py                    # Shared fixtures
│   │                                  #   - Database fixtures (testcontainers)
│   │                                  #   - Mock HTTP responses (respx)
│   │                                  #   - Sample data factories
│   │                                  #   - Redis fixtures
│   │
│   ├── unit/
│   │   ├── init.py
│   │   ├── core/
│   │   │   ├── test_config.py
│   │   │   ├── test_models.py
│   │   │   └── test_utils/
│   │   │       ├── test_hashing.py
│   │   │       ├── test_rate_limit.py
│   │   │       ├── test_retry.py
│   │   │       ├── test_address.py
│   │   │       ├── test_backpressure.py
│   │   │       └── test_bloom_filter.py
│   │   │
│   │   ├── collector/
│   │   │   ├── test_engine.py
│   │   │   ├── test_scheduler.py
│   │   │   ├── test_rate_limiter.py
│   │   │   └── test_adapters/
│   │   │       ├── test_rest.py
│   │   │       ├── test_graphql.py
│   │   │       ├── test_websocket.py
│   │   │       ├── test_json_rpc.py
│   │   │       ├── test_defillama.py
│   │   │       ├── test_coingecko.py
│   │   │       ├── test_github.py
│   │   │       ├── test_snapshot.py
│   │   │       ├── test_ccxt_adapter.py
│   │   │       └── test_ethereum.py
│   │   │
│   │   ├── validator/
│   │   │   ├── test_pipeline.py
│   │   │   ├── test_structural.py
│   │   │   ├── test_temporal.py
│   │   │   ├── test_semantic.py
│   │   │   ├── test_statistical.py
│   │   │   ├── test_cross_source.py
│   │   │   └── test_rules/
│   │   │       ├── test_price_rules.py
│   │   │       └── test_tvl_rules.py
│   │   │
│   │   ├── normalizer/
│   │   │   ├── test_engine.py
│   │   │   ├── test_deduplicator.py
│   │   │   ├── test_schemas/
│   │   │   │   ├── test_protocol.py
│   │   │   │   └── test_market.py
│   │   │   └── test_mappers/
│   │   │       ├── test_defillama_mapper.py
│   │   │       ├── test_coingecko_mapper.py
│   │   │       └── test_github_mapper.py
│   │   │
│   │   ├── enrichment/
│   │   │   ├── test_pipeline.py
│   │   │   ├── test_embeddings.py
│   │   │   ├── test_ner.py
│   │   │   ├── test_summarizer.py
│   │   │   ├── test_risk_scorer.py
│   │   │   └── test_relationship.py
│   │   │
│   │   ├── storage/
│   │   │   ├── test_manager.py
│   │   │   ├── test_lineage.py
│   │   │   └── test_cache.py
│   │   │
│   │   ├── analysis/
│   │   │   ├── test_anomaly.py
│   │   │   ├── test_correlation.py
│   │   │   ├── test_scorecard.py
│   │   │   ├── test_risk_cascade.py
│   │   │   └── test_graph_analytics.py
│   │   │
│   │   ├── delivery/
│   │   │   ├── test_api/
│   │   │   │   ├── test_protocols.py
│   │   │   │   ├── test_chains.py
│   │   │   │   ├── test_market.py
│   │   │   │   └── test_intelligence.py
│   │   │   │
│   │   │   ├── test_intelligence/
│   │   │   │   ├── test_daily_brief.py
│   │   │   │   └── test_protocol_deep_dive.py
│   │   │   │
│   │   │   └── test_alerts/
│   │   │       ├── test_engine.py
│   │   │       └── test_rules.py
│   │   │
│   │   └── orchestrator/
│   │       ├── test_engine.py
│   │       ├── test_dag.py
│   │       ├── test_scheduler.py
│   │       ├── test_state.py
│   │       └── test_backpressure.py
│   │
│   ├── integration/
│   │   ├── init.py
│   │   ├── test_collection_to_storage.py   # Full collection pipeline
│   │   ├── test_storage_roundtrip.py       # Write + read + verify
│   │   ├── test_enrichment_pipeline.py     # Enrichment end-to-end
│   │   ├── test_analysis_pipeline.py       # Analysis end-to-end
│   │   ├── test_api_endpoints.py           # API end-to-end
│   │   └── test_alert_pipeline.py          # Alert end-to-end
│   │
│   ├── e2e/
│   │   ├── init.py
│   │   ├── test_full_pipeline.py      # Full pipeline smoke test
│   │   └── test_intelligence_generation.py  # Intelligence product generation
│   │
│   ├── fixtures/
│   │   ├── init.py
│   │   ├── factories.py               # Data factories (factory_boy)
│   │   ├── sample_responses/
│   │   │   ├── defillama/
│   │   │   │   ├── protocols.json
│   │   │   │   ├── protocol_aave.json
│   │   │   │   ├── tvl_ethereum.json
│   │   │   │   └── pools.json
│   │   │   │
│   │   │   ├── coingecko/
│   │   │   │   ├── coins_list.json
│   │   │   │   ├── coin_ethereum.json
│   │   │   │   └── market_chart.json
│   │   │   │
│   │   │   ├── github/
│   │   │   │   ├── repos.json
│   │   │   │   ├── commits.json
│   │   │   │   └── contributors.json
│   │   │   │
│   │   │   ├── snapshot/
│   │   │   │   ├── proposals.json
│   │   │   │   └── votes.json
│   │   │   │
│   │   │   ├── ethereum_rpc/
│   │   │   │   ├── get_block.json
│   │   │   │   ├── get_logs.json
│   │   │   │   └── eth_call.json
│   │   │   │
│   │   │   └── flashbots/
│   │   │       ├── blocks.json
│   │   │       └── relay_data.json
│   │   │
│   │   └── sample_normalized/
│   │       ├── protocol_aave.json
│   │       ├── chain_ethereum.json
│   │       └── token_eth.json
│   │
│   └── performance/
│       ├── init.py
│       ├── bench_collection.py        # Collection throughput benchmarks
│       ├── bench_validation.py        # Validation throughput benchmarks
│       ├── bench_normalization.py     # Normalization throughput benchmarks
│       ├── bench_storage.py           # Storage write throughput benchmarks
│       └── bench_search.py            # Vector search latency benchmarks
│
├── notebooks/
│   ├── 01_data_exploration.ipynb      # Explore collected data
│   ├── 02_protocol_analysis.ipynb     # Interactive protocol analysis
│   ├── 03_graph_visualization.ipynb   # Knowledge graph visualization
│   ├── 04_anomaly_tuning.ipynb        # Anomaly detection threshold tuning
│   ├── 05_embedding_analysis.ipynb    # Embedding space visualization
│   └── 06_correlation_study.ipynb     # Cross-protocol correlation study
│
├── dune_queries/
│   ├── README.md
│   ├── protocol_metrics/
│   │   ├── uniswap_v3_daily.sql
│   │   ├── aave_v3_daily.sql
│   │   ├── lido_daily.sql
│   │   └── ...
│   ├── chain_metrics/
│   │   ├── ethereum_daily.sql
│   │   ├── l2_comparison.sql
│   │   └── ...
│   ├── mev/
│   │   ├── mev_daily_summary.sql
│   │   ├── builder_dominance.sql
│   │   └── ...
│   └── stablecoins/
│       ├── stablecoin_supply.sql
│       └── stablecoin_velocity.sql
│
└── docs/
├── architecture/
│   ├── overview.md                # Architecture overview
│   ├── data_flow.md               # Data flow diagrams
│   ├── storage_strategy.md        # Storage architecture details
│   ├── enrichment_pipeline.md     # GPU enrichment details
│   └── deployment.md              # Deployment guide
│
├── sources/
│   ├── source_catalog.md          # Complete source catalog
│   ├── reliability_assessment.md  # Source reliability analysis
│   └── adding_new_source.md       # Guide for adding new sources
│
├── schemas/
│   ├── protocol_schema.md         # Protocol schema documentation
│   ├── chain_schema.md            # Chain schema documentation
│   └── data_dictionary.md         # Complete data dictionary
│
├── operations/
│   ├── runbook.md                 # Operations runbook
│   ├── troubleshooting.md         # Troubleshooting guide
│   ├── backup_restore.md          # Backup/restore procedures
│   └── scaling.md                 # Scaling guide
│
├── api/
│   ├── api_reference.md           # API reference (auto-generated)
│   └── examples.md                # API usage examples
│
└── research/
├── methodology.md             # Research methodology
├── data_quality.md            # Data quality framework
└── limitations.md             # Known limitations
Copy

## IMPLEMENTATION ORDER (for Claude Code)

Execute in this exact order. Each phase builds on the previous.

### PHASE 1: Foundation (implement first)

src/chainscope/core/           — ALL files (config, models, enums, exceptions, utils)
config/                         — ALL YAML configurations
infrastructure/docker/          — ALL Dockerfiles
docker-compose.yml              — Full service composition
infrastructure/migrations/      — ALL database schemas
infrastructure/scripts/         — Init and migration scripts

Copy
### PHASE 2: Collection Layer

src/chainscope/collector/engine.py
src/chainscope/collector/scheduler.py
src/chainscope/collector/task.py + result.py
src/chainscope/collector/rate_limiter/     — ALL files
src/chainscope/collector/adapters/base.py
src/chainscope/collector/adapters/generic/ — ALL generic adapters
src/chainscope/collector/adapters/blockchain/ — Start with ethereum.py, evm_generic.py
src/chainscope/collector/adapters/aggregators/ — Start with defillama.py, coingecko.py
src/chainscope/collector/adapters/market/ccxt_unified.py
src/chainscope/collector/adapters/governance/ — snapshot.py, forums.py
src/chainscope/collector/adapters/security/  — ALL
src/chainscope/collector/adapters/developer/  — github_deep.py, npm.py
src/chainscope/collector/adapters/research/   — arxiv.py, protocol_docs.py
src/chainscope/collector/adapters/mev/         — ALL
src/chainscope/collector/adapters/social/      — farcaster.py, reddit.py
src/chainscope/collector/adapters/regulatory/  — ALL
src/chainscope/collector/adapters/indexers/    — the_graph.py
src/chainscope/collector/_registry.py

Copy
### PHASE 3: Validation + Normalization

src/chainscope/validator/       — ALL files
src/chainscope/normalizer/      — ALL files

Copy
### PHASE 4: Storage Layer

src/chainscope/storage/manager.py
src/chainscope/storage/timescale/  — ALL
src/chainscope/storage/neo4j/      — ALL
src/chainscope/storage/qdrant/     — ALL
src/chainscope/storage/clickhouse/ — ALL
src/chainscope/storage/redis/      — ALL
src/chainscope/storage/object_store/ — ALL
src/chainscope/storage/lineage/    — ALL

Copy
### PHASE 5: Enrichment (GPU)

src/chainscope/enrichment/pipeline.py
src/chainscope/enrichment/embeddings/  — ALL
src/chainscope/enrichment/nlp/         — ALL
src/chainscope/enrichment/scoring/     — ALL
src/chainscope/enrichment/graph/       — ALL

Copy
### PHASE 6: Analysis

src/chainscope/analysis/engine.py
src/chainscope/analysis/anomaly/       — ALL
src/chainscope/analysis/correlation/   — ALL
src/chainscope/analysis/scoring/       — ALL
src/chainscope/analysis/risk/          — ALL
src/chainscope/analysis/queries/       — ALL
src/chainscope/analysis/graph/         — ALL

Copy
### PHASE 7: Delivery

src/chainscope/delivery/api/           — ALL (FastAPI app + routes)
src/chainscope/delivery/intelligence/  — ALL (report generators)
src/chainscope/delivery/alerts/        — ALL
src/chainscope/delivery/exports/       — ALL

Copy
### PHASE 8: Orchestration

src/chainscope/orchestrator/           — ALL
src/chainscope/monitoring/             — ALL
src/chainscope/cli/                    — ALL

Copy
### PHASE 9: Testing

tests/conftest.py + fixtures/
tests/unit/         — ALL (aim for >85% coverage)
tests/integration/  — ALL
tests/e2e/          — ALL
tests/performance/  — ALL

Copy
### PHASE 10: Documentation + Ops

docs/               — ALL
notebooks/          — ALL
dune_queries/       — ALL
infrastructure/monitoring/  — Grafana dashboards, alerts
README.md           — Comprehensive project README

Copy

## KEY IMPLEMENTATION PRINCIPLES

```python
"""
RULES FOR CLAUDE CODE — Follow these strictly:

1. ASYNC EVERYWHERE
   - All I/O operations must be async (httpx, asyncpg, etc.)
   - Use asyncio.TaskGroup for parallel operations
   - Never call sync I/O in async context

2. PYDANTIC V2 FOR ALL DATA MODELS
   - Use model_validator, field_validator
   - ConfigDict for all models
   - Strict mode where appropriate

3. DEPENDENCY INJECTION
   - No global singletons
   - Pass dependencies through constructors
   - FastAPI Depends() for API layer

4. CONFIGURATION
   - Load from YAML/TOML via pydantic-settings
   - Environment variable overrides
   - No hardcoded values (URLs, thresholds, timeouts)

5. ERROR HANDLING
   - Custom exception hierarchy
   - Never catch bare Exception
   - Always log with context
   - Circuit breaker for external services

6. RATE LIMITING
   - Redis-backed distributed rate limiter
   - Per-domain configuration
   - Respect HTTP 429 + Retry-After
   - Respect robots.txt

7. IDEMPOTENCY
   - Content-hash based deduplication
   - Upsert operations (ON CONFLICT DO UPDATE)
   - Retry-safe operations

8. OBSERVABILITY
   - structlog for all logging (JSON, with trace_id)
   - prometheus_client for metrics
   - OpenTelemetry for distributed tracing
   - Every external call gets a span

9. TESTING
   - respx for HTTP mocking
   - testcontainers for database tests
   - hypothesis for property-based testing
   - pytest-asyncio for async tests

10. DATA QUALITY
    - Every data point has a confidence score
    - Every data point has lineage
    - Cross-validation when multiple sources exist
    - Anomaly detection flags, never silently drops
"""
````
