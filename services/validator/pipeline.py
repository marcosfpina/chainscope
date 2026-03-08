# services/validator/pipeline.py

"""
VALIDATION PIPELINE
Cada dado passa por múltiplos estágios de validação antes de ser persistido
"""

@dataclass
class ValidationResult:
    is_valid: bool
    confidence_score: float       # 0-1
    issues: list[str]
    corrections_applied: list[str]
    cross_validation_status: str  # "confirmed" | "unconfirmed" | "conflicting"
    corroborating_sources: list[str]


class ValidationPipeline:
    """
    Estágios de validação (executados em ordem):

    1. STRUCTURAL VALIDATION
       - JSON Schema compliance
       - Required fields present
       - Data types correct
       - Value ranges plausible

    2. TEMPORAL VALIDATION
       - Timestamp is not in the future
       - Timestamp is not too old (stale data)
       - Temporal ordering is consistent
       - No gaps in time series

    3. SEMANTIC VALIDATION
       - TVL values are non-negative
       - Percentages are 0-100 (or 0-1)
       - Addresses are valid format (checksum)
       - Chain IDs are known
       - Token symbols match addresses
       - Market cap = price × supply

    4. STATISTICAL VALIDATION (anomaly detection)
       - Z-score check against rolling window
       - Percentage change threshold
       - Volume/TVL ratio sanity
       - Price deviation from multiple sources
       - Outlier detection (IQR method)

    5. CROSS-SOURCE VALIDATION
       - Compare price from CoinGecko vs CCXT vs DefiLlama
       - Compare TVL from DefiLlama vs protocol's own data
       - Compare dev activity from GitHub vs npm
       - Flag discrepancies > threshold
       - Use median when sources conflict

    6. FRESHNESS VALIDATION
       - Is this data newer than what we have?
       - Is the source data fresh (not cached stale)?
       - Are dependent data points also fresh?
    """

    async def validate(self, data: RawDataPoint) -> ValidationResult:
        results = []

        results.append(await self.structural_validation(data))
        results.append(await self.temporal_validation(data))
        results.append(await self.semantic_validation(data))
        results.append(await self.statistical_validation(data))
        results.append(await self.cross_source_validation(data))
        results.append(await self.freshness_validation(data))

        return self.aggregate_results(results)


# ── Cross-Source Validation Rules ──

CROSS_VALIDATION_RULES = {
    "price": {
        "primary": "ccxt_aggregated",
        "secondary": ["coingecko", "coinmarketcap", "defillama_coins"],
        "max_deviation_pct": 2.0,
        "strategy": "median_of_sources",
    },
    "tvl": {
        "primary": "defillama",
        "secondary": ["protocol_native", "the_graph"],
        "max_deviation_pct": 5.0,
        "strategy": "prefer_primary_unless_stale",
    },
    "supply": {
        "primary": "on_chain_query",
        "secondary": ["coingecko", "messari"],
        "max_deviation_pct": 1.0,
        "strategy": "prefer_on_chain",
    },
    "dev_activity": {
        "primary": "github_api",
        "secondary": ["github_archive", "electric_capital"],
        "strategy": "union_with_dedup",
    },
}
