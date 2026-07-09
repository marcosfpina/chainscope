# services/collector/adapters/discourse.py

"""
DiscourseAdapter — coleta fóruns de governance via Discourse API REST.

Discourse expõe uma API REST padronizada em todos os fóruns, o que permite
um único adapter cobrir todos os targets de governance do CHAINSCOPE.

Targets configurados:
    MakerDAO    https://forum.makerdao.com
    Aave        https://governance.aave.com
    Arbitrum    https://forum.arbitrum.foundation
    Optimism    https://gov.optimism.io
    ENS         https://discuss.ens.domains
    Lido        https://research.lido.fi
    Compound    https://www.comp.xyz
    Uniswap     https://gov.uniswap.org
    Balancer    https://forum.balancer.fi
    Curve       https://gov.curve.fi
    dYdX        https://dydx.forum
    Frax        https://gov.frax.finance

Discourse endpoints usados:
    /latest.json              → tópicos recentes
    /top.json?period=weekly   → tópicos mais ativos da semana
    /categories.json          → categorias (mapeia governance vs. general)
    /t/{id}.json              → tópico completo com posts
    /posts.json               → posts globais
    /search.json?q={query}    → busca full-text

Uso:
    adapter = DiscourseAdapter()
    async for dp in adapter.collect({
        "forum_url": "https://forum.uniswap.org",
        "endpoint": "latest",
    }):
        process(dp)
"""

import json
from datetime import datetime, timezone
from typing import AsyncIterator

import httpx

from services.collector.adapters.base import RawDataPoint
from services.collector.adapters.web_adapter import WebSourceAdapter


# Fóruns Discourse cobertos pelo CHAINSCOPE
DISCOURSE_FORUMS = {
    "makerdao": "https://forum.makerdao.com",
    "aave": "https://governance.aave.com",
    "arbitrum": "https://forum.arbitrum.foundation",
    "optimism": "https://gov.optimism.io",
    "ens": "https://discuss.ens.domains",
    "lido": "https://research.lido.fi",
    "compound": "https://www.comp.xyz",
    "uniswap": "https://gov.uniswap.org",
    "balancer": "https://forum.balancer.fi",
    "curve": "https://gov.curve.fi",
    "dydx": "https://dydx.forum",
    "frax": "https://gov.frax.finance",
}


class DiscourseAdapter(WebSourceAdapter):
    """
    Coleta fóruns de governance via Discourse API REST padronizada.

    A API JSON do Discourse não requer autenticação para leitura de conteúdo
    público — basta adicionar `.json` ao endpoint ou passar header Accept.

    Estratégia de coleta:
    1. /latest.json — stream de novos tópicos (polling incremental)
    2. /top.json?period=weekly — tópicos quentes (sinal de relevância)
    3. /t/{id}.json — conteúdo completo de tópicos de interesse
    4. /search.json?q=... — busca por palavras-chave de governance

    Para respeitar os fóruns de comunidade, usa preset "stealth":
    3 concurrent requests, delay 2-5s, com user-agent rotation.
    """

    SOURCE_TIER = 3

    DISCOURSE_ENDPOINTS = {
        "latest": "/latest.json",
        "top": "/top.json?period=weekly",
        "categories": "/categories.json",
        "topic": "/t/{topic_id}.json",
        "posts": "/posts.json",
        "search": "/search.json?q={query}",
    }

    def __init__(self) -> None:
        super().__init__(preset="stealth")

    # ── Contrato BaseAdapter ─────────────────────────────────────────────────

    async def health_check(self) -> bool:
        """
        Verifica acessibilidade dos fóruns principais.
        Testa /categories.json no fórum da Uniswap como proxy de saúde.
        """
        test_url = f"{DISCOURSE_FORUMS['uniswap']}{self.DISCOURSE_ENDPOINTS['categories']}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(test_url, headers={"Accept": "application/json"})
                return resp.status_code == 200
        except Exception:
            return False

    async def collect(self, params: dict) -> AsyncIterator[RawDataPoint]:
        """
        Coleta um endpoint Discourse e retorna RawDataPoints.

        params:
            forum_url (str): URL base do fórum (ex: "https://gov.uniswap.org").
                             Pode ser chave de DISCOURSE_FORUMS (ex: "uniswap").
            endpoint (str): Chave de DISCOURSE_ENDPOINTS ou URL completa.
                            Default: "latest".
            topic_id (int): Necessário quando endpoint == "topic".
            query (str): Necessário quando endpoint == "search".
            forum_name (str): Nome semântico para source_id. Default: domain.
        """
        forum_url = params["forum_url"]
        if forum_url in DISCOURSE_FORUMS:
            forum_url = DISCOURSE_FORUMS[forum_url]
        forum_url = forum_url.rstrip("/")

        endpoint_key = params.get("endpoint", "latest")
        endpoint_path = self._resolve_endpoint(endpoint_key, params)

        forum_name = params.get("forum_name") or _domain_slug(forum_url)
        source_id = f"discourse.{forum_name}.{endpoint_key}"

        target_url = f"{forum_url}{endpoint_path}"

        # Usa SpiderNix com preset stealth para respeitar os fóruns
        results = await self._spider.crawl(
            start_url=target_url,
            max_pages=1,
            follow_links=False,
        )

        for result in results:
            dp = self._to_raw_data_point(result, source_id)

            # Tenta parsear o JSON da resposta Discourse
            dp = self._enrich_discourse_payload(dp, forum_url, forum_name, endpoint_key)

            if await self.validate_response(dp):
                yield dp

    async def validate_response(self, data: RawDataPoint) -> bool:
        """Valida que o payload é JSON Discourse válido."""
        base_ok = await super().validate_response(data)
        if not base_ok:
            return False

        payload = data.raw_payload
        if isinstance(payload, dict):
            # JSON já foi parseado — verifica estrutura mínima Discourse
            return bool(payload)
        if isinstance(payload, str):
            try:
                parsed = json.loads(payload)
                return isinstance(parsed, dict) and bool(parsed)
            except (json.JSONDecodeError, ValueError):
                return False
        return False

    def get_rate_limit_config(self) -> dict:
        return {
            "preset": "stealth",
            "note": "Discourse community forums — stealth preset (3 concurrent, 2-5s delay)",
            **self.get_rate_limit_stats(),
        }

    def get_schema(self) -> dict:
        return {
            "type": "object",
            "description": "Discourse API response (topic list, topic detail, or search results)",
            "properties": {
                "topic_list": {
                    "type": "object",
                    "properties": {
                        "topics": {"type": "array"},
                    },
                },
                "post_stream": {
                    "type": "object",
                    "properties": {
                        "posts": {"type": "array"},
                    },
                },
                "results": {"type": "array"},  # search endpoint
            },
        }

    # ── Helpers internos ─────────────────────────────────────────────────────

    def _resolve_endpoint(self, endpoint_key: str, params: dict) -> str:
        """Resolve endpoint key → path, substituindo variáveis."""
        template = self.DISCOURSE_ENDPOINTS.get(endpoint_key, endpoint_key)
        return template.format(
            topic_id=params.get("topic_id", ""),
            query=params.get("query", ""),
        )

    def _enrich_discourse_payload(
        self,
        dp: RawDataPoint,
        forum_url: str,
        forum_name: str,
        endpoint_key: str,
    ) -> RawDataPoint:
        """
        Tenta parsear o payload como JSON e enriquecer o metadata do RawDataPoint
        com informações específicas do Discourse (contagem de posts, categorias, etc.).
        """
        raw = dp.raw_payload
        parsed: dict | None = None

        if isinstance(raw, str):
            try:
                parsed = json.loads(raw)
                dp.raw_payload = parsed
            except (json.JSONDecodeError, ValueError):
                pass
        elif isinstance(raw, dict):
            parsed = raw

        if parsed:
            meta = {
                "forum_url": forum_url,
                "forum_name": forum_name,
                "endpoint": endpoint_key,
            }

            # Enriquece com contadores do endpoint
            if "topic_list" in parsed:
                topics = parsed["topic_list"].get("topics", [])
                meta["topic_count"] = len(topics)
                meta["topics_sample"] = [
                    {"id": t.get("id"), "title": t.get("title"), "posts_count": t.get("posts_count")}
                    for t in topics[:5]
                ]
            elif "post_stream" in parsed:
                posts = parsed["post_stream"].get("posts", [])
                meta["post_count"] = len(posts)
                meta["topic_id"] = parsed.get("id")
                meta["topic_title"] = parsed.get("title")
            elif "results" in parsed:
                meta["result_count"] = len(parsed["results"])

            dp.metadata.update(meta)

            # Corrige data_timestamp se temos created_at do tópico mais recente
            if "topic_list" in parsed:
                topics = parsed.get("topic_list", {}).get("topics", [])
                if topics and topics[0].get("created_at"):
                    try:
                        dp.data_timestamp = datetime.fromisoformat(
                            topics[0]["created_at"].replace("Z", "+00:00")
                        )
                    except (ValueError, KeyError):
                        pass

        return dp


# ── Helpers de módulo ────────────────────────────────────────────────────────

def _domain_slug(url: str) -> str:
    """Extrai slug do domínio: 'https://gov.uniswap.org' → 'gov.uniswap.org'."""
    from urllib.parse import urlparse
    return urlparse(url).netloc.replace(".", "_")
