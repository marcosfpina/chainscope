// services/graph/schema.cypher

// ══════════════════════════════════
// KNOWLEDGE GRAPH SCHEMA
// ══════════════════════════════════

// ── Node Types ──

// Protocol
CREATE CONSTRAINT protocol_id IF NOT EXISTS
FOR (p:Protocol) REQUIRE p.protocol_id IS UNIQUE;

// Chain
CREATE CONSTRAINT chain_id IF NOT EXISTS
FOR (c:Chain) REQUIRE c.chain_id IS UNIQUE;

// Token
CREATE CONSTRAINT token_id IF NOT EXISTS
FOR (t:Token) REQUIRE t.token_id IS UNIQUE;

// Organization (company, DAO, foundation)
CREATE CONSTRAINT org_id IF NOT EXISTS
FOR (o:Organization) REQUIRE o.org_id IS UNIQUE;

// Person (founder, researcher, core dev)
CREATE CONSTRAINT person_id IF NOT EXISTS
FOR (pe:Person) REQUIRE pe.person_id IS UNIQUE;

// Technology (consensus, VM, proof system)
CREATE CONSTRAINT tech_id IF NOT EXISTS
FOR (te:Technology) REQUIRE te.tech_id IS UNIQUE;

// AuditFirm
CREATE CONSTRAINT audit_firm_id IF NOT EXISTS
FOR (a:AuditFirm) REQUIRE a.firm_id IS UNIQUE;

// Vulnerability
CREATE CONSTRAINT vuln_id IF NOT EXISTS
FOR (v:Vulnerability) REQUIRE v.vuln_id IS UNIQUE;

// ResearchPaper
CREATE CONSTRAINT paper_id IF NOT EXISTS
FOR (r:ResearchPaper) REQUIRE r.paper_id IS UNIQUE;

// GovernanceProposal
CREATE CONSTRAINT proposal_id IF NOT EXISTS
FOR (g:GovernanceProposal) REQUIRE g.proposal_id IS UNIQUE;

// ── Relationship Types ──

// Protocol → Chain
// (:Protocol)-[:DEPLOYED_ON {tvl_usd, deployment_date, contracts}]->(:Chain)

// Protocol → Protocol
// (:Protocol)-[:FORKED_FROM {fork_date, modifications}]->(:Protocol)
// (:Protocol)-[:DEPENDS_ON {dependency_type}]->(:Protocol)
// (:Protocol)-[:COMPETES_WITH {overlap_category}]->(:Protocol)
// (:Protocol)-[:INTEGRATES_WITH {integration_type}]->(:Protocol)
// (:Protocol)-[:BRIDGES_TO {bridge_protocol}]->(:Protocol)

// Protocol → Technology
// (:Protocol)-[:USES_TECHNOLOGY {since, version}]->(:Technology)

// Protocol → Token
// (:Protocol)-[:HAS_TOKEN {role: "governance"|"utility"|"gas"}]->(:Token)

// Protocol → Organization
// (:Protocol)-[:DEVELOPED_BY]->(:Organization)
// (:Protocol)-[:FUNDED_BY {round, amount, date}]->(:Organization)
// (:Protocol)-[:AUDITED_BY {date, report_url}]->(:AuditFirm)

// Person → Organization
// (:Person)-[:WORKS_AT {role, since}]->(:Organization)
// (:Person)-[:FOUNDED]->(:Organization)

// Person → Protocol
// (:Person)-[:CONTRIBUTES_TO {commits, role}]->(:Protocol)

// Chain → Chain
// (:Chain)-[:SETTLES_ON]->(:Chain)  // L2 → L1
// (:Chain)-[:IBC_CONNECTED]->(:Chain)  // Cosmos chains

// Token → Token
// (:Token)-[:WRAPPED_VERSION_OF]->(:Token)
// (:Token)-[:PEGGED_TO]->(:Token)
// (:Token)-[:LP_TOKEN_FOR {pool_address}]->(:Token)

// Vulnerability → Protocol
// (:Vulnerability)-[:AFFECTED {date, loss_usd}]->(:Protocol)

// Research → Technology
// (:ResearchPaper)-[:INTRODUCES]->(:Technology)
// (:ResearchPaper)-[:ANALYZES]->(:Protocol)
