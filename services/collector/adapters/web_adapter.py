# services/collector/adapters/web_adapter.py

"""
WebSourceAdapter — wrapper de SpiderNix.crawl() que implementa o contrato BaseAdapter.

Usado por adapters Tier 3-4 (web-based):
  - Fóruns Discourse (governance: MakerDAO, Aave, Arbitrum, Optimism...)
  - Documentação técnica / whitepapers
  - Blogs de protocolo / pesquisa
  - Research papers (arxiv, ethresear.ch)
  - Rekt.news e similares
  - Sites com JS pesado (via preset "browser")

Adapters API REST (Tier 1-2) usam RateLimitedMixin diretamente com httpx.

Preset mappings (spider-nix → CHAINSCOPE):
  "research"  → docs, whitepapers, academic papers (15 concurrent, 1-3s delay)
  "stealth"   → fóruns Discourse (3 concurrent, 2-5s delay)
  "browser"   → sites com JS pesado (2 concurrent, 3-7s delay)
  "api"       → não usar aqui (REST APIs usam httpx + RateLimitedMixin)
"""

import hashlib
from datetime import datetime, timezone
from typing import AsyncIterator

from spider_nix import SpiderNix, get_preset, ProxyRotator, RequestDeduplicator
from spider_nix import CaptchaDetector, SessionManager

from services.collector.adapters.base import BaseAdapter, RawDataPoint
from services.collector.adapters.rate_limited_mixin import RateLimitedMixin


class WebSourceAdapter(RateLimitedMixin, BaseAdapter):
    """
    Adapter base para fontes web (HTML crawling).

    Delega o transporte para SpiderNix, que traz:
    - AdaptiveRateLimiter e CircuitBreaker internos
    - ProxyRotator com health tracking
    - RequestDeduplicator por URL/content hash
    - CaptchaDetector
    - SessionManager para sessões autenticadas
    - Presets de configuração (stealth, research, browser)

    Subclasses devem sobrescrever collect() e, tipicamente, get_schema().
    """

    SOURCE_TIER = 3  # Tier 3: web scraping; subclasses podem sobrescrever

    def __init__(
        self,
        preset: str = "research",
        proxy_rotator: ProxyRotator | None = None,
        session_id: str | None = None,
        rate_limiter_kwargs: dict | None = None,
    ) -> None:
        """
        Args:
            preset: Preset do spider-nix a usar ("research", "stealth", "browser").
            proxy_rotator: ProxyRotator opcional para rotação de proxies.
            session_id: ID de sessão para SessionManager (autenticação).
            rate_limiter_kwargs: Kwargs extras para __init_rate_limiter__().
        """
        config = get_preset(preset)

        self._spider = SpiderNix(
            config=config,
            proxy_rotator=proxy_rotator,
            enable_adaptive_rate_limiting=True,
            enable_circuit_breaker=True,
            enable_deduplication=True,
        )
        self._deduplicator = RequestDeduplicator()
        self._captcha_detector = CaptchaDetector()
        self._session_manager = SessionManager()
        self._preset = preset

        # Inicializa RateLimitedMixin — usado para health_check e chamadas diretas
        rl = rate_limiter_kwargs or {}
        self.__init_rate_limiter__(**rl)

    # ── Contrato BaseAdapter ─────────────────────────────────────────────────

    async def health_check(self) -> bool:
        """
        Verifica se o spider consegue fazer um request básico.
        Subclasses devem sobrescrever com URL representativa da fonte.
        """
        return True  # SpiderNix valida na primeira chamada de crawl()

    async def collect(self, params: dict) -> AsyncIterator[RawDataPoint]:
        """
        Coleta uma URL via SpiderNix e converte CrawlResults em RawDataPoints.

        params esperados:
            url (str): URL a crawlear.
            source_id (str): Identificador da fonte (ex: "discourse.uniswap").
            follow_links (bool): Se deve seguir links. Default False.
            max_pages (int): Limite de páginas. Default 1.
        """
        url: str = params["url"]
        source_id: str = params.get("source_id", url)
        follow_links: bool = params.get("follow_links", False)
        max_pages: int = params.get("max_pages", 1)

        results = await self._spider.crawl(
            start_url=url,
            max_pages=max_pages,
            follow_links=follow_links,
        )

        for result in results:
            yield self._to_raw_data_point(result, source_id)

    async def validate_response(self, data: RawDataPoint) -> bool:
        """Valida que o RawDataPoint tem conteúdo mínimo esperado."""
        if data.http_status is None or data.http_status >= 400:
            return False
        if not data.raw_payload:
            return False
        is_captcha, _ = self._captcha_detector.detect(
            html_content=data.raw_payload if isinstance(data.raw_payload, str) else None,
            status_code=data.http_status,
        )
        return not is_captcha

    def get_rate_limit_config(self) -> dict:
        """Retorna config de rate limit do preset ativo."""
        return {
            "preset": self._preset,
            **self.get_rate_limit_stats(),
        }

    def get_schema(self) -> dict:
        """JSON Schema base para responses HTML. Subclasses especializam."""
        return {
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "status_code": {"type": "integer"},
                "content": {"type": "string"},
                "timestamp": {"type": "string", "format": "date-time"},
            },
            "required": ["url", "status_code", "content"],
        }

    # ── Conversão interna ────────────────────────────────────────────────────

    def _to_raw_data_point(self, result: object, source_id: str) -> RawDataPoint:
        """
        Converte CrawlResult (spider-nix) → RawDataPoint (CHAINSCOPE).

        Args:
            result: CrawlResult retornado por SpiderNix.crawl().
            source_id: Identificador semântico da fonte.
        """
        content = result.content if hasattr(result, "content") else ""
        status_code = result.status_code if hasattr(result, "status_code") else None
        url = result.url if hasattr(result, "url") else source_id
        headers = result.headers if hasattr(result, "headers") else {}
        metadata = result.metadata if hasattr(result, "metadata") else {}

        # Timestamp da coleta; usa result.timestamp se disponível
        ts_str = getattr(result, "timestamp", None)
        if ts_str:
            try:
                collection_ts = datetime.fromisoformat(ts_str)
            except ValueError:
                collection_ts = datetime.now(timezone.utc)
        else:
            collection_ts = datetime.now(timezone.utc)

        content_hash = hashlib.sha256(
            content.encode("utf-8", errors="replace")
        ).hexdigest()

        return RawDataPoint(
            source_id=source_id,
            source_tier=self.SOURCE_TIER,
            collection_timestamp=collection_ts,
            data_timestamp=collection_ts,
            raw_payload=content,
            content_hash=content_hash,
            schema_version="1.0",
            collection_method=f"spider_nix:{self._preset}",
            url_or_endpoint=url,
            http_status=status_code,
            response_headers=dict(headers) if headers else {},
            metadata={
                "preset": self._preset,
                "dedup_stats": self._deduplicator.get_stats(),
                **metadata,
            },
        )
