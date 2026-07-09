# services/api/architecture.py

"""
API LAYER — Como consumir os dados
"""

API_ARCHITECTURE = {

    "internal_api": {
        "framework": "FastAPI",
        "description": "API principal para consumo dos dados",
        "endpoint_groups": {

            "/protocols": {
                "GET /protocols": "Lista todos os protocolos monitorados",
                "GET /protocols/{id}": "Detail view completo de um protocolo",
                "GET /protocols/{id}/metrics": "Timeseries de métricas",
                "GET /protocols/{id}/health": "Health scorecard",
                "GET /protocols/{id}/risks": "Risk assessment",
                "GET /protocols/{id}/graph": "Relações no knowledge graph",
                "GET /protocols/{id}/similar": "Protocolos similares (vector search)",
                "GET /protocols/{id}/timeline": "Timeline de eventos",
                "GET /protocols/compare": "Comparação lado a lado",
            },

            "/chains": {
                "GET /chains": "Lista todas as chains",
                "GET /chains/{id}": "Detail view de uma chain",
                "GET /chains/{id}/protocols": "Protocolos na chain",
                "GET /chains/{id}/metrics": "Métricas da chain",
                "GET /chains/{id}/l2-analysis": "L2 specific analysis",
            },

            "/market": {
                "GET /market/overview": "Market overview global",
                "GET /market/stablecoins": "Stablecoin dashboard",
                "GET /market/dex-volumes": "DEX volume por chain/protocol",
                "GET /market/funding-rates": "Funding rates cross-exchange",
                "GET /market/liquidations": "Liquidation data",
                "GET /market/mev": "MEV landscape",
            },

            "/governance": {
                "GET /governance/active": "Propostas ativas cross-DAO",
                "GET /governance/{protocol}": "Governance de um protocolo",
                "GET /governance/delegates": "Top delegates cross-DAO",
            },

            "/security": {
                "GET /security/audits": "Auditorias recentes",
                "GET /security/incidents": "Incidentes de segurança",
                "GET /security/bounties": "Bug bounties ativos",
                "GET /security/risk-map": "Mapa de risco do ecossistema",
            },

            "/developers": {
                "GET /developers/activity": "Dev activity por ecossistema",
                "GET /developers/trending-repos": "Repos trending",
                "GET /developers/migrations": "Developer migration flows",
            },

            "/research": {
                "GET /research/papers": "Papers recentes",
                "GET /research/search": "Semantic search no corpus",
                "POST /research/query": "Natural language query",
            },

            "/alerts": {
                "GET /alerts": "Alertas ativos",
                "GET /alerts/anomalies": "Anomalias detectadas",
                "POST /alerts/subscribe": "Subscribe a alertas",
            },

            "/intelligence": {
                "GET /intelligence/daily-brief": "Daily intelligence brief",
                "GET /intelligence/weekly-report": "Weekly deep report",
                "GET /intelligence/scenarios": "Scenario analysis results",
                "POST /intelligence/custom-query": "Custom analytical query",
            },

            "/meta": {
                "GET /meta/sources": "Status de todas as fontes",
                "GET /meta/health": "Pipeline health dashboard",
                "GET /meta/quality": "Data quality metrics",
                "GET /meta/lineage/{record_id}": "Lineage de um dado",
                "GET /meta/coverage": "Coverage map (o que temos vs gaps)",
            },
        }
    },
}
