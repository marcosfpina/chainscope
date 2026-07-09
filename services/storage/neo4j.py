# services/storage/neo4j.py

"""
Neo4jClient — knowledge graph storage para relações entre entidades DeFi.

Driver: neo4j[async] (neo4j.AsyncGraphDatabase)

Casos de uso:
    Protocolo --FORKS_FROM--> Protocolo
    Protocolo --DEPLOYED_ON--> Chain
    Hack      --EXPLOITED-->   Protocolo
    Wallet    --VOTED_ON-->    Proposal
    Token     --ISSUED_BY-->   Protocolo

ENV:
    NEO4J_URI       — bolt://localhost:7687
    NEO4J_USER      — neo4j
    NEO4J_PASSWORD  — neo4j

Uso:
    client = Neo4jClient()
    await client.connect()
    await client.upsert_node("Protocol", "id", {"id": "uniswap", "name": "Uniswap"})
    await client.upsert_relationship("uniswap", "DEPLOYED_ON", "ethereum", {})
    await client.close()
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

import structlog

log = structlog.get_logger(__name__)


class Neo4jClient:
    """
    Cliente async para Neo4j.

    Usa neo4j[async] — AsyncGraphDatabase.driver().

    Métodos principais:
        connect()              — abre o driver (lazy sessions)
        close()                — fecha o driver
        upsert_node()          — MERGE de um nó por label + propriedade-chave
        upsert_relationship()  — MERGE de uma relação entre dois nós por ID
        run_query()            — executa Cypher arbitrário, retorna list[dict]
    """

    def __init__(
        self,
        uri: str | None = None,
        user: str | None = None,
        password: str | None = None,
    ) -> None:
        self._uri = uri or os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        self._user = user or os.environ.get("NEO4J_USER", "neo4j")
        self._password = password or os.environ.get("NEO4J_PASSWORD", "neo4j")
        self._driver = None

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    async def connect(self) -> None:
        """
        Abre o driver Neo4j async.
        Tenta conexão com retry exponencial (útil em docker-compose).
        """
        self._driver = await _create_driver_with_retry(
            uri=self._uri,
            user=self._user,
            password=self._password,
        )
        log.info(
            "neo4j.connected",
            uri=self._uri.split("@")[-1] if "@" in self._uri else self._uri,
        )

    async def close(self) -> None:
        """Fecha o driver e libera recursos."""
        if self._driver:
            await self._driver.close()
            self._driver = None
            log.info("neo4j.closed")

    # ── Write ──────────────────────────────────────────────────────────────────

    async def upsert_node(
        self,
        label: str,
        id_prop: str,
        props: dict[str, Any],
    ) -> None:
        """
        MERGE de um nó pelo label e propriedade-chave.

        Cria se não existir, atualiza propriedades se existir.

        Args:
            label   — Label Neo4j (ex: "Protocol", "Chain", "Wallet")
            id_prop — Nome da propriedade usada como chave de identidade (ex: "id")
            props   — Todas as propriedades do nó (deve conter id_prop)
        """
        if id_prop not in props:
            raise ValueError(
                f"upsert_node: id_prop '{id_prop}' ausente em props"
            )
        cypher = (
            f"MERGE (n:{label} {{{id_prop}: $id_val}}) "
            "SET n += $props "
            "RETURN n"
        )
        params = {"id_val": props[id_prop], "props": props}
        await self.run_query(cypher, params)
        log.debug("neo4j.node_upserted", label=label, id=props[id_prop])

    async def upsert_relationship(
        self,
        from_id: str,
        rel_type: str,
        to_id: str,
        props: dict[str, Any] | None = None,
        from_label: str = "",
        to_label: str = "",
    ) -> None:
        """
        MERGE de uma relação entre dois nós identificados por `.id`.

        Args:
            from_id    — id do nó de origem
            rel_type   — tipo da relação (ex: "FORKS_FROM", "DEPLOYED_ON")
            to_id      — id do nó de destino
            props      — propriedades da relação (opcional)
            from_label — label do nó de origem (opcional, melhora performance)
            to_label   — label do nó de destino (opcional)
        """
        from_pattern = f"(a:{from_label} {{id: $from_id}})" if from_label else "(a {id: $from_id})"
        to_pattern = f"(b:{to_label} {{id: $to_id}})" if to_label else "(b {id: $to_id})"
        cypher = (
            f"MATCH {from_pattern} "
            f"MATCH {to_pattern} "
            f"MERGE (a)-[r:{rel_type}]->(b) "
            "SET r += $props "
            "RETURN r"
        )
        params = {
            "from_id": from_id,
            "to_id": to_id,
            "props": props or {},
        }
        await self.run_query(cypher, params)
        log.debug(
            "neo4j.rel_upserted",
            from_id=from_id,
            rel=rel_type,
            to_id=to_id,
        )

    async def upsert_nodes_batch(
        self,
        label: str,
        id_prop: str,
        nodes: list[dict[str, Any]],
    ) -> int:
        """
        MERGE em batch de nós do mesmo label.

        Usa UNWIND para eficiência em grandes volumes.

        Returns:
            Número de nós processados.
        """
        if not nodes:
            return 0
        cypher = (
            "UNWIND $nodes AS props "
            f"MERGE (n:{label} {{{id_prop}: props.{id_prop}}}) "
            "SET n += props "
            "RETURN count(n) AS total"
        )
        result = await self.run_query(cypher, {"nodes": nodes})
        count = result[0]["total"] if result else len(nodes)
        log.debug("neo4j.batch_upserted", label=label, count=count)
        return int(count)

    # ── Read ───────────────────────────────────────────────────────────────────

    async def run_query(
        self,
        cypher: str,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Executa Cypher arbitrário e retorna lista de dicts.

        Args:
            cypher — query Cypher
            params — parâmetros da query

        Returns:
            Lista de dicts com os campos retornados pelo RETURN.
        """
        driver = self._get_driver()
        async with driver.session() as session:
            result = await session.run(cypher, parameters=params or {})
            records = await result.data()
            return records

    async def get_node(
        self,
        label: str,
        id_value: str,
        id_prop: str = "id",
    ) -> dict[str, Any] | None:
        """Busca um nó pelo label e id."""
        cypher = f"MATCH (n:{label} {{{id_prop}: $id_val}}) RETURN n"
        result = await self.run_query(cypher, {"id_val": id_value})
        if not result:
            return None
        node = result[0].get("n")
        return dict(node) if node else None

    async def get_neighbors(
        self,
        node_id: str,
        rel_type: str | None = None,
        direction: str = "out",
    ) -> list[dict[str, Any]]:
        """
        Retorna vizinhos de um nó via relação.

        Args:
            node_id  — id do nó de origem
            rel_type — tipo de relação (None = qualquer)
            direction — "out" | "in" | "both"
        """
        rel = f":{rel_type}" if rel_type else ""
        if direction == "out":
            pattern = f"(a {{id: $id}})-[r{rel}]->(b)"
        elif direction == "in":
            pattern = f"(a {{id: $id}})<-[r{rel}]-(b)"
        else:
            pattern = f"(a {{id: $id}})-[r{rel}]-(b)"
        cypher = f"MATCH {pattern} RETURN b, type(r) AS rel_type"
        result = await self.run_query(cypher, {"id": node_id})
        return [
            {"node": dict(r["b"]), "rel_type": r["rel_type"]}
            for r in result
        ]

    # ── Internal ──────────────────────────────────────────────────────────────

    def _get_driver(self):
        if self._driver is None:
            raise RuntimeError("Neo4jClient: chame connect() primeiro")
        return self._driver


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _create_driver_with_retry(
    uri: str,
    user: str,
    password: str,
    max_retries: int = 5,
):
    """Cria driver async com retry exponencial em falhas de conexão."""
    try:
        from neo4j import AsyncGraphDatabase
    except ImportError as exc:
        raise RuntimeError(
            "neo4j não instalado — adicione 'neo4j' ao pyproject.toml"
        ) from exc

    delay = 1.0
    last_exc: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            driver = AsyncGraphDatabase.driver(
                uri,
                auth=(user, password),
            )
            # Verifica conectividade
            await driver.verify_connectivity()
            return driver
        except Exception as exc:
            last_exc = exc
            log.warning(
                "neo4j.connection_retry",
                attempt=attempt,
                retry_in=delay,
                exc=str(exc),
            )
        await asyncio.sleep(delay)
        delay = min(delay * 2, 30.0)

    raise RuntimeError(
        f"Neo4j: falhou após {max_retries} tentativas — {last_exc}"
    )
