# services/enrichment/pipeline.py

"""
ENRICHMENT PIPELINE — Usa o LLM na B300 para enriquecer dados
"""

class EnrichmentPipeline:
    """
    Estágios de enriquecimento:

    1. ENTITY EXTRACTION (NER)
       - Input: whitepapers, forum posts, research papers
       - Output: entidades extraídas (protocolos, pessoas, tecnologias, tokens)
       - Model: Fine-tuned NER ou LLM prompting

    2. RELATIONSHIP MAPPING
       - Input: entidades extraídas
       - Output: edges no knowledge graph
       - Types: "uses_technology", "forked_from", "competes_with",
                "invested_by", "founded_by", "audited_by",
                "bridges_to", "built_on", "depends_on"

    3. DOCUMENT SUMMARIZATION
       - Input: whitepapers, audit reports, research papers
       - Output: structured summaries com key points
       - Focus: technical innovation, risks, trade-offs

    4. SENTIMENT ANALYSIS (para social data)
       - Input: tweets, forum posts, reddit
       - Output: sentiment score + reasoning
       - Calibration: crypto-specific (WAGMI ≠ positive technical signal)

    5. TECHNOLOGY CLASSIFICATION
       - Input: repo code, documentation
       - Output: technology stack classification
       - Labels: consensus type, VM type, proof system, DA solution

    6. RISK SCORING
       - Input: all protocol data
       - Output: composite risk score
       - Factors: centralization, audit coverage, bug bounty,
                  upgrade mechanism, token concentration, time since deploy

    7. EMBEDDING GENERATION
       - Input: all text content
       - Output: embeddings para vector search
       - Model: sentence-transformers ou similar
       - Storage: Qdrant
    """

    async def enrich(self, normalized_data: dict) -> dict:
        enrichments = {}

        # NER sobre textos
        if "text_content" in normalized_data:
            enrichments["entities"] = await self.extract_entities(
                normalized_data["text_content"]
            )

        # Embeddings para search
        enrichments["embeddings"] = await self.generate_embeddings(
            normalized_data
        )

        # Risk scoring
        if normalized_data["type"] == "protocol":
            enrichments["risk_score"] = await self.compute_risk_score(
                normalized_data
            )

        # Technology classification
        if "technology" in normalized_data:
            enrichments["tech_classification"] = await self.classify_technology(
                normalized_data["technology"]
            )

        return enrichments
