# CHAINSCOPE

> Enterprise-grade research pipeline for deep intelligence on the cryptocurrency ecosystem.
> Collects **exclusively public data** — no PII, no sensitive data.
> LLM inference on B300.

```
┌──────────┐   ┌──────────────┐   ┌──────────┐   ┌─────────────┐
│  COLLECT │──▶│  NORMALIZE   │──▶│  ANALYZE │──▶│   DELIVER   │
│  LAYER   │   │  LAYER       │   │  LAYER   │   │  LAYER      │
└──────────┘   └──────────────┘   └──────────┘   └─────────────┘
     │               │                 │                │
┌──────────┐   ┌──────────────┐   ┌──────────┐   ┌─────────────┐
│ VALIDATE │   │    ENRICH    │   │CORRELATE │   │  VISUALIZE  │
│  LAYER   │   │  LAYER (B300)│   │  LAYER   │   │  LAYER      │
└──────────┘   └──────────────┘   └──────────┘   └─────────────┘

              STORAGE: TIMESERIES + VECTOR + GRAPH + ANALYTICS
```

---

## What it does

CHAINSCOPE monitors and correlates the entire public crypto ecosystem:

- **Protocols & DeFi** — TVL, volumes, fees, revenue, yields across 500+ protocols
- **On-chain data** — blocks, transactions, validators, governance, staking (15+ chains)
- **Developer activity** — commits, contributors, releases across key GitHub orgs
- **Governance** — proposals, votes, delegates from 12 major governance forums
- **Security** — audit findings, exploit tracking, bug bounties, risk scoring
- **Research** — whitepapers, arxiv papers, ethresear.ch, industry reports
- **Market microstructure** — orderbook, funding rates, open interest, MEV/PBS
- **ZK & L2 technology** — proof system benchmarks, L2Beat risk analysis, rollup stages

---

## Architecture

### Data Source Tiers

| Tier | Type | Reliability | Examples |
|------|------|-------------|---------|
| 1 | On-chain direct (RPC) | 0.99 | Ethereum, Solana, Cosmos, Polkadot, L2s |
| 1.5 | On-chain indexed | 0.93 | The Graph, Dune, Flipside, Nansen, Arkham |
| 2 | Protocol aggregators | 0.88 | DefiLlama, CoinGecko, L2Beat, Token Terminal |
| 2.5 | Market microstructure | 0.90 | CCXT (100+ exchanges), Flashbots, MEV relays |
| 3 | Governance & dev | 0.90 | Snapshot, Tally, GitHub, audit databases |
| 3.5 | Research & knowledge | 0.85 | arxiv, IACR, ethresear.ch, industry research |
| 4 | Social & sentiment | 0.60 | Farcaster, Reddit, regulatory filings |

### Adapter Hierarchy

```
BaseAdapter                          ← abstract contract
├── RateLimitedMixin                 ← AdaptiveRateLimiter + CircuitBreaker
│   │  (spider-nix components)
│   └── WebSourceAdapter            ← SpiderNix.crawl() for HTML/web sources
│       ├── DiscourseAdapter        ← 12 governance forums
│       ├── DocsAdapter             ← whitepapers, protocol docs
│       └── ResearchAdapter         ← arxiv, ethresear.ch
│
└── Tier 1/2 adapters (direct)
    ├── EthereumRPCAdapter          ← JSON-RPC + Beacon API
    ├── GraphQLAdapter              ← The Graph, Snapshot, Tally
    ├── DefiLlamaAdapter            ← TVL, volumes, fees, hacks
    └── CoinGeckoAdapter            ← prices, market data
```

### Storage

| Engine | Purpose |
|--------|---------|
| **TimescaleDB** | Time-series: prices, TVL, metrics, on-chain data |
| **Qdrant** | Vector DB: embeddings for semantic search over docs |
| **Neo4j** | Knowledge graph: protocol→chain→tech→person relationships |
| **ClickHouse** | Analytics: aggregated queries at scale |
| **Redis** | Cache, rate limit state, message broker |

### Knowledge Graph (Neo4j)

Nodes: `Protocol`, `Chain`, `Token`, `Organization`, `Person`, `Technology`, `AuditFirm`, `Vulnerability`, `ResearchPaper`, `GovernanceProposal`

Key relationships:
- `(:Protocol)-[:DEPLOYED_ON]->(:Chain)`
- `(:Protocol)-[:FORKED_FROM]->(:Protocol)`
- `(:Protocol)-[:DEPENDS_ON]->(:Protocol)` — cascading risk
- `(:Protocol)-[:USES_TECHNOLOGY]->(:Technology)`
- `(:Protocol)-[:AUDITED_BY]->(:AuditFirm)`
- `(:Chain)-[:SETTLES_ON]->(:Chain)` — L2 → L1
- `(:ResearchPaper)-[:INTRODUCES]->(:Technology)`

---

## Stack

```
Python 3.12+        asyncio-first, Pydantic v2
httpx / aiohttp     HTTP + WebSocket clients
web3.py             Ethereum JSON-RPC + ABI decoding
gql[aiohttp]        GraphQL (The Graph, Snapshot, Tally)
spider-nix          Transport engine for web/HTML sources (Tier 3-4)
  ├── AdaptiveRateLimiter   backpressure-aware, per-domain
  ├── CircuitBreaker        3-state fault tolerance
  ├── ProxyRotator          health-aware proxy selection
  └── SpiderNix.crawl()     stealth HTML crawling
structlog           structured logging
prometheus-client   metrics
opentelemetry       distributed tracing
apscheduler         job scheduling
```

---

## Getting started

### Prerequisites

- Nix with flakes enabled
- Docker + Docker Compose
- SSH access to `github.com/marcosfpina`

### Dev shell

```bash
git clone git@github.com:marcosfpina/chainscope.git
cd chainscope
nix develop
```

The shell provides Python 3.13 with all deps, database CLIs, and sets all environment variables pointing to local Docker services.

### Start infra

```bash
docker compose -f infra/docker-compose.foundation.yml up -d
```

Services started:
- TimescaleDB on `:5432`
- Redis on `:6379`
- Neo4j on `:7474` / `:7687`
- Qdrant on `:6333`
- ClickHouse on `:8123`

### Run the pipeline

```bash
# Collector (continuous)
python -m services.collector.engine

# API (FastAPI delivery layer)
python -m services.delivery.api.app

# Enrichment (requires B300 inference service)
INFERENCE_URL=http://b300-host:9000 python -m services.enrichment.pipeline
```

---

## NixOS integration

CHAINSCOPE is available as a NixOS module via the system flake:

```nix
# /etc/nixos/hosts/<host>/configuration.nix
kernelcore.blockchain.chainscope = {
  enable          = true;
  enableCollector = true;
  enableApi       = true;
  inferenceUrl    = "http://b300:9000";
};
```

This enables:
- `chainscope-collector.service` — continuous collection pipeline
- `chainscope-api.service` — FastAPI on port 8420
- Shell aliases: `chainscope-infra-up`, `chainscope-logs`, `chainscope-status`

---

## Research domains

```yaml
protocol_fundamentals   on_chain_analytics    governance
tokenomics              developer_activity    security_audits
regulatory_landscape    market_microstructure cross_chain_interop
mev_analysis            defi_mechanics        zk_technology
consensus_mechanisms    layer2_scaling        bridge_security
```

---

## License

Apache License 2.0 — see [LICENSE](LICENSE).

Collects exclusively public data from public APIs and public web sources.
No personal data, no private keys, no credentials are stored or processed.
