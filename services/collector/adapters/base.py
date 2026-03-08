# services/collector/adapters/base.py

"""
ADAPTER BASE — Cada fonte implementa este contrato

Hierarquia de adapters do CHAINSCOPE:

    BaseAdapter                          ← contrato obrigatório (esta classe)
    ├── RateLimitedMixin                 ← rate_limited_mixin.py
    │   │  AdaptiveRateLimiter + CircuitBreaker (spider-nix)
    │   │  Usar diretamente em: Tier 1 (JSON-RPC), Tier 1.5 (GraphQL)
    │   │
    │   └── WebSourceAdapter             ← web_adapter.py
    │       │  SpiderNix.crawl() + ProxyRotator + RequestDeduplicator
    │       │  Usar em: Tier 3-4 (web scraping, fóruns, docs, blogs)
    │       │
    │       ├── DiscourseAdapter         ← discourse.py
    │       ├── DocsAdapter              ← (futuro)
    │       └── ResearchAdapter          ← (futuro)
    │
    └── (direto) Tier 1/1.5 adapters
        ├── EthereumRPCAdapter           ← (futuro) JSON-RPC
        ├── GraphQLAdapter               ← (futuro) The Graph, Snapshot
        └── DefiFlamaAdapter             ← (existente) REST API
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import AsyncIterator


@dataclass
class RawDataPoint:
    """Unidade atômica de dado coletado"""
    source_id: str
    source_tier: int           # 1-5
    collection_timestamp: datetime
    data_timestamp: datetime   # quando o dado foi gerado
    raw_payload: dict | list | str
    content_hash: str          # SHA-256 do payload
    schema_version: str
    collection_method: str
    url_or_endpoint: str
    http_status: int | None
    response_headers: dict | None
    metadata: dict             # source-specific metadata


class BaseAdapter(ABC):
    """Interface que todo collector deve implementar"""

    @abstractmethod
    async def health_check(self) -> bool:
        """Verifica se a fonte está acessível"""
        ...

    @abstractmethod
    async def collect(self, params: dict) -> AsyncIterator[RawDataPoint]:
        """Coleta dados — yield de RawDataPoints"""
        ...

    @abstractmethod
    async def validate_response(self, data: RawDataPoint) -> bool:
        """Validação source-specific do response"""
        ...

    @abstractmethod
    def get_rate_limit_config(self) -> dict:
        """Retorna configuração de rate limit"""
        ...

    @abstractmethod
    def get_schema(self) -> dict:
        """JSON Schema esperado do output"""
        ...


# ── Exemplo: DefiLlama Adapter ──

class DefiLlamaAdapter(BaseAdapter):
    """
    Collector para DeFiLlama API
    Sem autenticação necessária
    Rate limit: reasonable use
    """

    BASE_URL = "https://api.llama.fi"

    ENDPOINTS = {
        "protocols": "/v2/protocols",
        "protocol": "/protocol/{slug}",
        "tvl_chain": "/v2/historicalChainTvl/{chain}",
        "tvl_protocol": "/v2/historicalChainTvl",
        "stablecoins": "/stablecoins",
        "stablecoin": "/stablecoin/{id}",
        "stablecoin_chains": "/stablecoinchains",
        "pools": "/pools",
        "pool": "/pool/{pool_id}",
        "bridges": "/bridges",
        "bridge": "/bridge/{id}",
        "bridge_volume": "/bridge/{id}/volume",
        "volumes_dex": "/overview/dexs",
        "volumes_dex_chain": "/overview/dexs/{chain}",
        "fees": "/overview/fees",
        "fees_chain": "/overview/fees/{chain}",
        "protocol_fees": "/summary/fees/{protocol}",
        "raises": "/raises",
        "hacks": "/hacks",
        "treasuries": "/treasury/{protocol}",
        "emissions": "/emissions/{protocol}",
        "governance": "/governance/{protocol}",
        "active_users": "/activeUsers/{chain}",
        "coins_current": "/prices/current/{coins}",
        "coins_historical": "/coins/prices/historical/{timestamp}/{coins}",
        "coins_chart": "/coins/chart/{coins}",
        "coins_percentage": "/coins/percentage/{coins}",
        "coins_batch_historical": "/batchHistorical",
    }

    async def collect(self, params: dict) -> AsyncIterator[RawDataPoint]:
        endpoint = params["endpoint"]
        # ... implementação completa
        pass

    async def collect_all_protocols(self) -> AsyncIterator[RawDataPoint]:
        """Coleta lista completa de protocolos com TVL"""
        pass

    async def collect_protocol_deep(self, slug: str) -> AsyncIterator[RawDataPoint]:
        """Deep dive em um protocolo específico:
        - TVL por chain
        - TVL histórico
        - Token info
        - Fees/revenue (se disponível)
        - Treasury
        - Governance
        - Raises
        - Hacks relacionados
        """
        pass

    async def collect_yields_universe(self) -> AsyncIterator[RawDataPoint]:
        """Universo completo de yields/pools"""
        pass

    async def collect_stablecoin_landscape(self) -> AsyncIterator[RawDataPoint]:
        """Panorama completo de stablecoins"""
        pass


# ── Exemplo: GitHub Deep Scanner ──

class GitHubDeepAdapter(BaseAdapter):
    """
    Scanner profundo de atividade de desenvolvimento
    """

    async def scan_organization(self, org: str) -> AsyncIterator[RawDataPoint]:
        """
        Para cada org:
        1. Lista todos os repos
        2. Para cada repo:
           a. Commit frequency (último ano)
           b. Contributors + commit count
           c. Open/Closed PRs (últimos 90 dias)
           d. Open/Closed Issues
           e. Releases (últimos 12 meses)
           f. Languages breakdown
           g. Dependencies (package.json, Cargo.toml, go.mod)
           h. CI/CD activity (Actions)
           i. README/docs quality assessment
        3. Cross-repo dependency graph
        4. Contributor overlap com outros projetos
        """
        pass

    async def track_key_repos(self, repos: list[str]) -> AsyncIterator[RawDataPoint]:
        """
        Monitoramento de repos específicos de alta importância:
        - ethereum/consensus-specs
        - ethereum/execution-specs
        - ethereum/EIPs
        - paradigmxyz/reth
        - matter-labs/zksync-era
        - scroll-tech/scroll
        - etc.
        """
        pass
