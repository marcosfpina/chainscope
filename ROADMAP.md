# CHAINSCOPE — ROADMAP DE IMPLEMENTAÇÃO

> Pipeline de inteligência enterprise para pesquisa profunda de criptomoedas.
> Coleta exclusivamente dados públicos. Sem PII. Sem dados sensíveis.
> Inferência LLM na B300. Transport layer: spider-nix.

---

## ESTADO ATUAL

```
COMPLETO   arch.md                         Arquitetura visual do sistema
COMPLETO   config/pipeline.yml             Config mestre (quality, rate limits, domains)
COMPLETO   config/protocol_universe.py     Universo de protocolos monitorados
COMPLETO   infra/docker-compose.yml        Stack: TimescaleDB, Qdrant, Neo4j, Redis, ClickHouse
COMPLETO   pyproject.toml                  Dependências + spider-nix como path dep
COMPLETO   services/collector/source_taxonomy.py     5 tiers de fontes mapeados
COMPLETO   services/collector/engine.py              Schedules + CollectionTask dataclass
COMPLETO   services/collector/adapters/base.py       Contrato BaseAdapter + RawDataPoint
COMPLETO   services/collector/adapters/rate_limited_mixin.py   AdaptiveRateLimiter + CircuitBreaker
COMPLETO   services/collector/adapters/web_adapter.py          SpiderNix wrapper (Tier 3-4)
COMPLETO   services/collector/adapters/discourse.py            Governance forums (12 fóruns)
COMPLETO   services/normalizer/schemas.py            PROTOCOL_SCHEMA normalizado
COMPLETO   services/validator/pipeline.py            6 estágios de validação
COMPLETO   services/enrichment/pipeline.py           LLM enrichment (NER, embed, risk)
COMPLETO   services/analysis/correlation.py          Correlation engine (6 análises)
COMPLETO   services/analysis/query_library.py        Analytical queries pré-programadas
COMPLETO   services/delivery/intelligence_products.py  Intelligence products (daily brief, etc.)
COMPLETO   services/orchestrator/dag.py              DAG de execução do pipeline
COMPLETO   services/graph/schema.cypher              Neo4j knowledge graph schema
COMPLETO   services/monitoring/config.py             Observabilidade
COMPLETO   services/api/architecture.py              FastAPI layer design
ESQUELETO  services/storage/architecture.py          Storage clients (a implementar)
PENDENTE   flake.nix                                 Ambiente Nix reproduzível
```

---

## FASES DE IMPLEMENTAÇÃO

### FASE 1 — FUNDAÇÃO (Infra + Adapters Core)
**Objetivo**: pipeline funcionando end-to-end com dados reais das fontes mais simples.

#### 1.1 Infra (Docker Compose)
- [ ] Subir `docker-compose.foundation.yml`
- [ ] Validar conectividade: TimescaleDB, Qdrant, Neo4j, Redis, ClickHouse
- [ ] Migrations TimescaleDB: tabelas de séries temporais (preços, TVL, métricas)
- [ ] Migrations Neo4j: constraints e índices do `schema.cypher`
- [ ] Migrations ClickHouse: tabelas de analytics agregados

#### 1.2 Storage Clients
Implementar `services/storage/`:
- [ ] `timescale.py` — asyncpg, upsert de timeseries, hypertable management
- [ ] `neo4j_client.py` — neo4j-driver, merge de nodes/edges, cypher helpers
- [ ] `qdrant_client.py` — qdrant-client, upsert de vectors, collection management
- [ ] `clickhouse.py` — clickhouse-connect, batch inserts, materialized views
- [ ] `redis_client.py` — redis.asyncio, cache get/set, rate limit state
- [ ] `lineage.py` — rastreio de proveniência (fonte → transformação → storage)

#### 1.3 Adapters REST (Tier 2 — sem autenticação)
Implementar usando `RateLimitedMixin` + `httpx`:
- [ ] `adapters/defillama.py` — TVL, volumes, fees, hacks, yields, bridges
- [ ] `adapters/coingecko.py` — preços, market data, categorias, trending
- [ ] `adapters/l2beat.py` — TVL L2, risk analysis, stage classification
- [ ] `adapters/token_terminal.py` — revenue, earnings, P/E de protocolos

#### 1.4 Adapters On-Chain (Tier 1 — JSON-RPC)
Implementar usando `web3.py` + `httpx` + `RateLimitedMixin`:
- [ ] `connectors/ethereum.py` — blocos, txs, logs, estado, beacon chain
- [ ] `connectors/solana.py` — blocos, txs, accounts, vote accounts
- [ ] `connectors/cosmos.py` — LCD REST + gRPC, IBC, governance, staking

#### 1.5 Normalizer Engine
- [ ] `normalizer/engine.py` — orchestra mappers, detecta schema, chama deduplicator
- [ ] `normalizer/mappers/defillama_mapper.py` — DefiLlama → PROTOCOL_SCHEMA
- [ ] `normalizer/mappers/coingecko_mapper.py` — CoinGecko → PROTOCOL_SCHEMA
- [ ] `normalizer/deduplicator.py` — content_hash + semantic dedup via Qdrant

**Entrega FASE 1**: coletar TVL/preços de DefiLlama e CoinGecko, normalizar,
validar e persistir no TimescaleDB. Pipeline end-to-end sem LLM.

---

### FASE 2 — COLETA COMPLETA (Todos os Tiers)
**Objetivo**: cobrir todas as fontes do source_taxonomy.

#### 2.1 Adapters GraphQL (Tier 1.5)
- [ ] `adapters/graphql.py` — adapter genérico GraphQL (gql[aiohttp])
- [ ] `adapters/the_graph.py` — subgraphs Uniswap, Aave, Compound, Lido, etc.
- [ ] `adapters/snapshot.py` — governance off-chain (proposals, votes, delegates)
- [ ] `adapters/tally.py` — governance on-chain (OpenZeppelin Governor)

#### 2.2 Adapters WebSocket (Real-time)
- [ ] `adapters/websocket.py` — adapter genérico WebSocket (aiohttp)
- [ ] `connectors/ethereum_stream.py` — new_heads, pending txs, logs stream
- [ ] `adapters/exchange_ws.py` — CCXT WebSocket (trades, orderbook, funding)

#### 2.3 Adapters Web (Tier 3-4, usando WebSourceAdapter)
- [ ] `adapters/github.py` — orgs, repos, commits, PRs, releases, contributors
- [ ] `adapters/arxiv.py` — papers cs.CR, cs.DC (blockchain, ZK, consensus)
- [ ] `adapters/rss.py` — adapter genérico RSS/Atom
- [ ] `adapters/rekt.py` — exploit postmortems (rekt.news RSS)
- [ ] `adapters/immunefi.py` — bug bounties, payouts

#### 2.4 Adapters MEV (Tier 5)
- [ ] `adapters/flashbots.py` — MEV explore, relay API, block submissions
- [ ] `adapters/mev_relays.py` — ultrasound, bloxroute, aestus (relay bids)
- [ ] `adapters/zeromev.py` — MEV classification, sandwich/arb/liquidation

#### 2.5 Scheduler
- [ ] `collector/scheduler.py` — APScheduler, cron por collection tier
- [ ] Schedules: realtime, 1min, 5min, 15min, hourly, 6h, daily, weekly, monthly

---

### FASE 3 — ENRICHMENT COM LLM (B300)
**Objetivo**: pipeline de enrichment rodando na B300 via inference service.

#### 3.1 Inference Service
- [ ] `services/inference/` — FastAPI que expõe modelo na B300
- [ ] Endpoints: `/embed`, `/ner`, `/summarize`, `/classify`, `/sentiment`
- [ ] Modelo base: configurável (LLaMA, Mistral, etc.)
- [ ] Batch processing: acumula N docs, processa em batch na GPU

#### 3.2 Enrichment Pipeline
Implementar `services/enrichment/`:
- [ ] `embeddings.py` — gera embeddings via `/embed`, upsert no Qdrant
- [ ] `ner.py` — extrai entidades (Protocol, Person, Technology, Token)
- [ ] `summarizer.py` — sumariza whitepapers, audit reports, papers
- [ ] `classifier.py` — classifica tecnologia (consensus, VM, proof system, DA)
- [ ] `risk_scorer.py` — score composto (centralização, audits, bug bounty, etc.)
- [ ] `sentiment.py` — sentimento calibrado para crypto (WAGMI ≠ sinal técnico)

#### 3.3 Knowledge Graph Population
- [ ] Mapper: entidades NER → Neo4j nodes
- [ ] Mapper: relações NER → Neo4j edges
- [ ] Relações: USES_TECHNOLOGY, FORKED_FROM, DEPENDS_ON, AUDITED_BY, etc.

---

### FASE 4 — ANALYTICS & INTELLIGENCE PRODUCTS
**Objetivo**: outputs consumíveis — scorecards, briefs, alertas.

#### 4.1 Correlation Engine
Implementar `services/analysis/`:
- [ ] `correlation.py` — cross-chain flows, dev migration, MEV patterns
- [ ] `anomaly.py` — anomalia em TVL, preços, gas, dev activity
- [ ] `risk_cascade.py` — blast radius se Chainlink/USDC falham
- [ ] `graph_analytics.py` — PageRank de protocolos, clustering de ecossistemas

#### 4.2 Analytical Queries
- [ ] `query_library.py` executável — rodar cada ANALYTICAL_QUERY no schedule
- [ ] Protocol Health Scorecard (diário)
- [ ] DEX Market Share Evolution (diário)
- [ ] ZK Technology Adoption (semanal)
- [ ] Developer Ecosystem Health (semanal)
- [ ] Cross-Chain TVL Flows (diário)

#### 4.3 Intelligence Products (gerados pelo LLM na B300)
- [ ] `delivery/daily_brief.py` — briefing diário às 06:00 UTC
- [ ] `delivery/protocol_deep_dive.py` — relatório profundo por protocolo
- [ ] `delivery/security_alert.py` — alertas de hack/exploit em tempo real
- [ ] `delivery/governance_digest.py` — digest semanal de proposals ativas

---

### FASE 5 — API & DELIVERY
**Objetivo**: consumir a inteligência via API e alertas.

#### 5.1 FastAPI
- [ ] `delivery/api/app.py` — FastAPI com rotas completas
- [ ] Routes: /protocols, /chains, /market, /governance, /security, /research
- [ ] Middleware: rate limiting, cache (Redis), CORS
- [ ] WebSocket endpoint para streaming de alertas real-time

#### 5.2 Observabilidade
- [ ] Prometheus metrics em todos os adapters (via `rate_limit_stats()`)
- [ ] Grafana dashboards: coleta, validação, enrichment, storage
- [ ] Alertas: fonte offline, spike de erros, circuit breaker aberto

---

## INTEGRAÇÃO spider-nix → chainscope

```
spider-nix é dependência de chainscope (pyproject.toml path dep)

Tier 1  JSON-RPC/WebSocket  ──→  connectors/ (httpx + web3 + RateLimitedMixin)
Tier 1.5 GraphQL            ──→  adapters/graphql.py (gql[aiohttp] + RateLimitedMixin)
Tier 2  REST APIs           ──→  adapters/*.py (httpx + RateLimitedMixin)
Tier 3-4 Web/HTML          ──→  WebSourceAdapter (SpiderNix.crawl())
                                 └── DiscourseAdapter (governance forums)
                                 └── DocsAdapter (whitepapers, docs)
                                 └── ResearchAdapter (arxiv, ethresear.ch)

Componentes spider-nix reutilizados:
  AdaptiveRateLimiter  → RateLimitedMixin (todos os adapters Tier 1-4)
  CircuitBreaker       → RateLimitedMixin (todos os adapters Tier 1-4)
  SpiderNix.crawl()    → WebSourceAdapter (Tier 3-4 HTML)
  ProxyRotator         → WebSourceAdapter (rotação para web scraping)
  RequestDeduplicator  → WebSourceAdapter (dedup URL/content)
  CaptchaDetector      → WebSourceAdapter (detecta bloqueios)
  SessionManager       → WebSourceAdapter (sessões autenticadas)
```

---

## HARDWARE — B300

```
Inference Service (services/inference/)
  Modelo: LLaMA 3.1 70B ou Mistral Large (configurável)
  Tasks offload para GPU:
    - Embedding generation (batch de 512 docs)
    - NER (Named Entity Recognition)
    - Document summarization
    - Technology classification
    - Sentiment analysis (crypto-calibrated)

  CPU tasks (não precisam de GPU):
    - Risk scoring (regras determinísticas)
    - Cross-source validation
    - Anomaly detection (scipy/sklearn)
    - Graph analytics (Neo4j queries)

  Estimativa de throughput (B300, ~1000 tokens/s):
    - Embeddings: ~2000 docs/hora (batch mode)
    - Summarization: ~200 documentos/hora
    - NER: ~1000 textos/hora
```

---

## PRÓXIMOS PASSOS IMEDIATOS

1. `nix develop` no chainscope (flake.nix pronto)
2. `docker compose up` para subir infra
3. Implementar `services/storage/timescale.py` (primeiro cliente)
4. Implementar `adapters/defillama.py` (primeira coleta real)
5. Rodar pipeline end-to-end: DefiLlama → Normalize → Validate → TimescaleDB
6. Adicionar CoinGecko, L2Beat
7. Subir inference service na B300
8. Ligar enrichment ao pipeline

---

## CONVENÇÕES DE CÓDIGO

```python
# 1. Todo adapter herda RateLimitedMixin OU WebSourceAdapter
class MyAdapter(RateLimitedMixin, BaseAdapter):
    def __init__(self):
        self.__init_rate_limiter__(initial_delay_ms=300.0)

# 2. _call_protected() envolve TODAS as chamadas externas
result = await self._call_protected(self._http_get, url)

# 3. Yield RawDataPoint — nunca retorna lista
async def collect(self, params) -> AsyncIterator[RawDataPoint]:
    ...
    yield raw_data_point

# 4. structlog em todo adapter
import structlog
log = structlog.get_logger(__name__)
log.info("collected", source=self.source_id, count=n)

# 5. Pydantic para todos os schemas de saída
class ProtocolMetrics(BaseModel):
    tvl_usd: float
    volume_24h: float
    ...
```
