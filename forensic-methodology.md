# Forensic Investigation Methodology

## Table of Contents
1. [Investigation Lifecycle](#1-investigation-lifecycle)
2. [Evidence Handling Standards](#2-evidence-handling-standards)
3. [Swarm Investigation Coordination](#3-swarm-investigation-coordination)
4. [Hypothesis-Driven Investigation](#4-hypothesis-driven-investigation)
5. [Entity Resolution Framework](#5-entity-resolution-framework)
6. [Temporal Analysis](#6-temporal-analysis)
7. [Network/Link Analysis](#7-networklink-analysis)
8. [Financial Flow Tracing](#8-financial-flow-tracing)
9. [Pattern Recognition](#9-pattern-recognition)
10. [Confidence & Source Assessment](#10-confidence--source-assessment)
11. [Legal & Ethical Framework](#11-legal--ethical-framework)

---

## 1. Investigation Lifecycle

### Phase 1: Mandate Definition
- Define investigation subject(s) - persons, entities, events, or topics
- Establish scope boundaries (timeframe, geography, domains)
- Identify preliminary research questions
- Set legal authority basis and ethical constraints
- Determine deliverable requirements (report length, detail level, jurisdiction)
- Create investigation charter document

### Phase 2: Source Identification
- Map all applicable data sources (see databases.md)
- Prioritize sources by relevance and accessibility
- Identify API endpoints, query parameters, and authentication needs
- Plan data collection cadence (real-time vs. batch vs. historical)
- Document source reliability baselines

### Phase 3: Data Collection (The Swarm)
- Execute parallel searches across all prioritized sources
- Collect raw data in native format with full provenance
- Apply consistent metadata tagging during collection
- Validate collection completeness against source map
- Identify gaps requiring alternative sources or techniques
- Save all outputs as structured CSV with chain of custody fields

### Phase 4: Processing & Normalization
- Deduplicate records across sources
- Normalize entity names (persons, companies, addresses)
- Resolve entity identities (same person across different records)
- Enrich data (geocoding, entity classification, relationship tagging)
- Validate data integrity (hash checks, format validation)
- Structure into investigation database

### Phase 5: Analysis & Synthesis
- Apply intelligence disciplines (see intelligence-methods.md)
- Construct entity-relationship graph
- Build comprehensive timeline
- Perform financial flow tracing
- Conduct pattern recognition across datasets
- Test hypotheses using ACH methodology
- Calculate confidence levels for all findings

### Phase 6: Report Production
- Write comprehensive forensic report (40,000+ words standard)
- Include all evidence with source citations
- Present entity graphs and visualizations
- Detail methodology and confidence assessments
- Provide executive summary with key findings
- Append all raw data and chain of custody records

### Phase 7: Review & Validation
- Verify all factual claims against source evidence
- Check for confirmation bias (did we test alternative hypotheses?)
- Validate source reliability assessments
- Ensure exculpatory evidence is included
- Peer review of analytical conclusions
- Final confidence calibration

## 2. Evidence Handling Standards

### Chain of Custody Requirements
Every piece of evidence must record:
```
- Evidence ID: Unique identifier
- Source: Origin URL/database/API endpoint
- Collection timestamp: UTC timestamp
- Collector: Swarm agent identifier
- Method: API query / web scrape / manual extraction
- Hash: SHA-256 of original content
- Format: File type and encoding
- Integrity verified: Yes/No with method
- Storage location: File path in evidence repository
```

### Evidence Classification
- **Class A**: Primary/original source documents (contracts, emails, databases)
- **Class B**: Official records (government filings, court documents)
- **Class C**: Professional journalism (investigative reports, verified stories)
- **Class D**: Open source intelligence (social media, forums, public data)
- **Class E**: Derived/secondary analysis (reports citing other sources)

### Corroboration Rules
- Critical claims require minimum 2 independent sources
- Class A evidence can stand alone with authentication
- Class D evidence requires corroboration for critical claims
- Single-source claims must be flagged with confidence level < 0.7

## 3. Swarm Investigation Coordination

### Parallel Search Strategy
```
Swarm Agent 1: Identity & PII Sources
  - DeHashed, LeakIX, HIBP, Snusbase
  - Search: email, username, phone, name variants
  
Swarm Agent 2: Document & Leak Archives
  - DDoSecrets, Cryptome, IntelX
  - Search: entity name, associated persons, timeframes
  
Swarm Agent 3: Corporate & Financial
  - OpenCorporates, ICIJ Aleph, OpenOwnership, EDGAR
  - Search: company names, directors, beneficial owners
  
Swarm Agent 4: Dark Web & Underground
  - Dread, XSS.is, Tor indexes, forum archives
  - Search: entity mentions, data offers, criminal discussions
  
Swarm Agent 5: Technical Infrastructure
  - Shodan, Censys, certificate logs, DNS
  - Search: domains, IPs, ASNs, certificates
  
Swarm Agent 6: Open Source & Media
  - News archives, court records, social media, academic
  - Search: entity name, events, timeline references
```

### Cross-Agent Coordination
- Shared evidence repository with real-time updates
- Entity resolution across agent boundaries
- Duplicate detection and merging
- Confidence score harmonization
- Anomaly flagging (conflicting evidence between agents)

## 4. Hypothesis-Driven Investigation

### Hypothesis Generation
1. Formulate primary hypothesis (what happened / who is responsible)
2. Generate 3-5 alternative hypotheses
3. Identify evidence that would support each hypothesis
4. Identify evidence that would disprove each hypothesis
5. Prioritize hypotheses by parsimony and evidence fit

### ACH Matrix Template
```
Hypotheses →  | H1: [Primary] | H2: [Alt 1] | H3: [Alt 2] | H4: [Alt 3]
Evidence ↓    |               |             |             |
--------------|---------------|-------------|-------------|-------------
Evidence 1    |     + / -     |    + / -    |    + / -    |   + / -
Evidence 2    |     + / -     |    + / -    |    + / -    |   + / -
Evidence 3    |     + / -     |    + / -    |    + / -    |   + / -
Consistency   |    % match    |   % match   |   % match   |  % match
```

### Deductive Chain Documentation
For every major conclusion, document:
```
CONCLUSION: [Statement]
CONFIDENCE: [0.0-1.0] + verbal (possible/probable/highly likely/certain)

DEDUCTION CHAIN:
1. [Premise] → Evidence: [ref], Confidence: [x]
2. [Inference] → Evidence: [ref], Confidence: [y]
3. [Conclusion] → Confidence: [x * y * ...]

ALTERNATIVE EXPLANATIONS CONSIDERED:
- [Alt 1]: Evidence against [ref], confidence reduction [z]
- [Alt 2]: Evidence against [ref], confidence reduction [w]

FINAL CONFIDENCE: [Calculated] [Verbal]
```

## 5. Entity Resolution Framework

### Resolution Signals
Match on combination of:
- Exact name match (with normalization)
- Partial name match + shared attribute (address, phone, email)
- Network proximity (connected to same entities)
- Temporal overlap (active during same periods)
- Geographic overlap (same locations)
- Behavioral pattern similarity

### Confidence Levels
- **Confirmed**: Multiple strong signals match, no contradictions
- **Probable**: Several signals match, minor differences explained
- **Possible**: Some signals match, alternative explanations exist
- **Unverified**: Single signal, requires more evidence
- **Disputed**: Contradictory evidence exists

## 6. Temporal Analysis

### Timeline Construction
- Extract all date-time references from evidence
- Normalize to UTC for global investigations
- Build master timeline with millisecond precision where possible
- Layer: Events, Communications, Financial transactions, Travel, Digital activity
- Identify temporal clusters (activity spikes, gaps)
- Calculate time-between-events for pattern detection

### Anomaly Detection
- Unusual activity hours (nighttime activity suggesting different timezone)
- Activity gaps (evidence destruction, operational pause)
- Acceleration patterns (increasing frequency before event)
- Synchronization (coordinated actions across entities)

## 7. Network/Link Analysis

### Graph Construction
Nodes: Persons, Companies, Addresses, Bank Accounts, Domains, IP Addresses, Phone Numbers, Email Addresses, Events
Edges: Ownership, Employment, Communication, Transaction, Co-location, Family, Association

### Centrality Analysis
- Degree centrality: Who has most connections
- Betweenness centrality: Who bridges different groups
- Eigenvector centrality: Who connects to important nodes
- Community detection: Identify clusters and subgroups

### Pattern Recognition
- Shell company indicators (circular ownership, nominee directors)
- Money laundering patterns (layering, structuring, rapid movement)
- Network insulation (cutouts, intermediaries)
- Coordinated behavior (synchronized actions, shared infrastructure)

## 8. Financial Flow Tracing

### Follow-the-Money Methodology
1. Identify starting point accounts/transactions
2. Map outgoing flows (layer by layer)
3. Identify intermediaries (shell companies, money mules, mixers)
4. Trace to endpoints (assets, cash withdrawals, other entities)
5. Map reverse flows (who funded the starting point)
6. Identify patterns (structuring, layering, integration)

### Cryptocurrency Tracing
- Address clustering (identify controlled addresses)
- Exchange identification (where funds enter/exit traditional finance)
- Mixer/tumbler detection
- Transaction timing analysis
- Cross-chain bridging analysis

### Traditional Finance Tracing
- Wire transfer analysis (SWIFT, correspondent banking)
- Shell company network mapping
- Real estate transaction tracking
- Cash-intensive business analysis
- Trade-based money laundering indicators

## 9. Pattern Recognition

### Criminal Scheme Indicators
- **Ponzi/Pyramid**: Recruitment patterns, payout structures, sustainability analysis
- **Money Laundering**: Layering complexity, velocity, structuring patterns
- **Bribery/Corruption**: Unusual payments, offshore intermediaries, PEP connections
- **Fraud**: Document inconsistencies, identity manipulation, financial anomalies
- **Human Trafficking**: Movement patterns, payment structures, communication networks
- **Cybercrime**: Infrastructure sharing, tool commonality, victim clustering
- **Sanctions Evasion**: Alternative entity names, transshipment routing, beneficial ownership hiding

### Behavioral Signatures
- Communication tradecraft (encryption habits, timing patterns)
- Operational security measures (and their failures)
- Linguistic patterns (writing style, language proficiency, recurring phrases)
- Technical fingerprints (tool preferences, coding style, infrastructure choices)

## 10. Confidence & Source Assessment

### Source Reliability Rating (NATO System)
| Rating | Description |
|--------|-------------|
| A | Completely reliable (verified history, official records) |
| B | Usually reliable (professional sources, established outlets) |
| C | Fairly reliable (some verification, consistent accuracy) |
| D | Not usually reliable (unverified, single-source) |
| E | Unreliable (history of inaccuracy, bias) |
| F | Cannot be judged |

### Information Credibility
| Rating | Description |
|--------|-------------|
| 1 | Confirmed (other independent confirmation) |
| 2 | Probably true |
| 3 | Possibly true |
| 4 | Doubtful |
| 5 | Improbable |
| 6 | Cannot be judged |

### Combined Confidence Matrix
A-1 = Highest confidence | F-6 = Lowest confidence
Always report confidence level with every significant finding.

## 11. Legal & Ethical Framework

### Governing Principles
1. **Truth and Accuracy**: Report facts as they are, not as desired
2. **Completeness**: Include all relevant evidence, including exculpatory
3. **Impartiality**: No predetermined conclusions; follow evidence
4. **Proportionality**: Scope of investigation matches severity of subject
5. **Legality**: All methods must comply with applicable law
6. **Human Rights**: Respect dignity, privacy rights, due process
7. **Transparency**: Methodology and limitations clearly disclosed
8. **Accountability**: All findings attributable to sources and evidence

### Natural Law Foundation
- Universal principles of justice transcend positive law
- Right to truth is fundamental
- Abuse of authority invalidates the authority
- Victims have right to remedy and restoration
- No person is above accountability
- Justice delayed is justice denied
- Evidence speaks truth regardless of power dynamics

### Rights of the Accused (Even Preliminary)
- Presumption of innocence until proven otherwise
- Right to know evidence against them
- Right to present counter-evidence
- Protection from arbitrary accusations
- Proportionality of response to evidence strength

### Output Commitments
- No fabrication, embellishment, or distortion of evidence
- Clear distinction between proven facts and inferences
- Confidence levels attached to all claims
- Alternative hypotheses presented fairly
- Full source attribution
- Methodology transparency
