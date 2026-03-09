# services/normalizer/engine.py

"""
NormalizerEngine — converte RawDataPoint em rows para TimescaleDB.

Dispatch por source_id + metadata["endpoint"]:

    source_id="defillama":
        endpoint="protocols"  → _normalize_defillama_protocols()
        endpoint="protocol"   → _normalize_defillama_protocol()
        endpoint="fees"       → _normalize_defillama_fees()
        endpoint="hacks"      → _normalize_defillama_hacks()
        endpoint="raises"     → (ignorado — sem métricas numéricas relevantes)
        endpoint="yields"     → (futuro)
"""

from __future__ import annotations

import structlog

from services.collector.adapters.base import RawDataPoint
from services.normalizer.mappers import coingecko_mapper, defillama_mapper

log = structlog.get_logger(__name__)


class NormalizerEngine:
    """
    Converte RawDataPoint em lista de rows para TimescaleClient.upsert_metrics_batch().

    Usage:
        engine = NormalizerEngine()
        rows = engine.normalize(dp)
        await client.upsert_metrics_batch(rows)
    """

    def normalize(self, dp: RawDataPoint) -> list[dict]:
        """
        Entry point de normalização.

        Retorna lista (possivelmente vazia) de rows prontos para upsert.
        Nunca levanta exceção — erros são logados e retornam lista vazia.
        """
        source = dp.source_id
        try:
            if source == "defillama":
                return self._normalize_defillama(dp)
            elif source == "coingecko":
                return self._normalize_coingecko(dp)
            else:
                log.warning("normalizer.unknown_source", source_id=source)
                return []
        except Exception as exc:
            log.error(
                "normalizer.error",
                source_id=source,
                endpoint=dp.metadata.get("endpoint"),
                exc=str(exc),
            )
            return []

    # ── DefiLlama ─────────────────────────────────────────────────────────────

    def _normalize_defillama(self, dp: RawDataPoint) -> list[dict]:
        endpoint = dp.metadata.get("endpoint", "protocols")
        collected_at = dp.collection_timestamp

        dispatch = {
            "protocols": self._normalize_defillama_protocols,
            "protocol":  self._normalize_defillama_protocol,
            "fees":      self._normalize_defillama_fees,
            "hacks":     self._normalize_defillama_hacks,
        }

        handler = dispatch.get(endpoint)
        if handler is None:
            log.debug("normalizer.defillama.skip_endpoint", endpoint=endpoint)
            return []

        rows = handler(dp)
        log.debug(
            "normalizer.defillama.done",
            endpoint=endpoint,
            rows=len(rows),
        )
        return rows

    def _normalize_defillama_protocols(self, dp: RawDataPoint) -> list[dict]:
        """Normaliza /v2/protocols — lista completa de protocolos."""
        payload = dp.raw_payload
        if not isinstance(payload, list):
            log.warning("normalizer.defillama.protocols.bad_type", got=type(payload).__name__)
            return []
        return defillama_mapper.map_protocols_list(payload, dp.collection_timestamp)

    def _normalize_defillama_protocol(self, dp: RawDataPoint) -> list[dict]:
        """Normaliza /protocol/{slug} — detalhe de um protocolo."""
        payload = dp.raw_payload
        slug = dp.metadata.get("slug", "")
        if not isinstance(payload, dict):
            log.warning("normalizer.defillama.protocol.bad_type", got=type(payload).__name__)
            return []
        if not slug:
            log.warning("normalizer.defillama.protocol.no_slug")
            return []
        return defillama_mapper.map_protocol_detail(payload, slug, dp.collection_timestamp)

    def _normalize_defillama_fees(self, dp: RawDataPoint) -> list[dict]:
        """Normaliza /overview/fees — fees e revenue de todos os protocolos."""
        payload = dp.raw_payload
        if not isinstance(payload, dict):
            log.warning("normalizer.defillama.fees.bad_type", got=type(payload).__name__)
            return []
        return defillama_mapper.map_fees_overview(payload, dp.collection_timestamp)

    def _normalize_defillama_hacks(self, dp: RawDataPoint) -> list[dict]:
        """Normaliza /hacks — histórico de exploits."""
        payload = dp.raw_payload
        if not isinstance(payload, list):
            log.warning("normalizer.defillama.hacks.bad_type", got=type(payload).__name__)
            return []
        return defillama_mapper.map_hacks(payload, dp.collection_timestamp)

    # ── CoinGecko ─────────────────────────────────────────────────────────────

    def _normalize_coingecko(self, dp: RawDataPoint) -> list[dict]:
        endpoint = dp.metadata.get("endpoint", "markets")
        collected_at = dp.collection_timestamp

        dispatch = {
            "markets":      self._normalize_coingecko_markets,
            "coin":         self._normalize_coingecko_coin,
            "market_chart": self._normalize_coingecko_market_chart,
            "global":       self._normalize_coingecko_global,
        }

        handler = dispatch.get(endpoint)
        if handler is None:
            log.debug("normalizer.coingecko.skip_endpoint", endpoint=endpoint)
            return []

        rows = handler(dp)
        log.debug(
            "normalizer.coingecko.done",
            endpoint=endpoint,
            rows=len(rows),
        )
        return rows

    def _normalize_coingecko_markets(self, dp: RawDataPoint) -> list[dict]:
        payload = dp.raw_payload
        if not isinstance(payload, list):
            log.warning("normalizer.coingecko.markets.bad_type", got=type(payload).__name__)
            return []
        return coingecko_mapper.map_coins_markets(payload, dp.collection_timestamp)

    def _normalize_coingecko_coin(self, dp: RawDataPoint) -> list[dict]:
        payload = dp.raw_payload
        coin_id = dp.metadata.get("id", "")
        if not isinstance(payload, dict):
            log.warning("normalizer.coingecko.coin.bad_type", got=type(payload).__name__)
            return []
        if not coin_id:
            coin_id = payload.get("id", "unknown")
        return coingecko_mapper.map_coin_detail(payload, coin_id, dp.collection_timestamp)

    def _normalize_coingecko_market_chart(self, dp: RawDataPoint) -> list[dict]:
        payload = dp.raw_payload
        coin_id = dp.metadata.get("id", "unknown")
        if not isinstance(payload, dict):
            log.warning("normalizer.coingecko.market_chart.bad_type", got=type(payload).__name__)
            return []
        return coingecko_mapper.map_market_chart(payload, coin_id, dp.collection_timestamp)

    def _normalize_coingecko_global(self, dp: RawDataPoint) -> list[dict]:
        payload = dp.raw_payload
        if not isinstance(payload, dict):
            log.warning("normalizer.coingecko.global.bad_type", got=type(payload).__name__)
            return []
        return coingecko_mapper.map_global(payload, dp.collection_timestamp)
