# Intelligence Disciplines & Methodology Reference

## Table of Contents
1. [OSINT - Open Source Intelligence](#1-osint)
2. [SIGINT - Signals Intelligence](#2-sigint)
3. [IMINT - Imagery Intelligence](#3-imint)
4. [GEOINT - Geospatial Intelligence](#4-geoint)
5. [MASINT - Measurement and Signature Intelligence](#5-masint)
6. [SOCMINT - Social Media Intelligence](#6-socmint)
7. [PsyOps - Psychological Operations](#7-psyops)
8. [HUMINT Principles in Digital Context](#8-humint-principles)
9. [Deductive Logic Framework](#9-deductive-logic-framework)
10. [Intelligence Cycle](#10-intelligence-cycle)
11. [Analytical Techniques](#11-analytical-techniques)

---

## 1. OSINT

**Definition**: Collection and analysis of publicly available information.

**Sources**: News, websites, forums, social media, public records, academic papers, conferences, corporate filings, WHOIS, DNS, certificates.

**Techniques**:
- Advanced search operators (Google Dorks, Bing operators)
- Cached content recovery (Google Cache, Wayback Machine, archive.today)
- Metadata extraction from documents (EXIF, Office metadata, PDF properties)
- WHOIS history and reverse WHOIS
- DNS enumeration and historical DNS
- SSL/TLS certificate transparency logs
- Social network analysis and connection mapping
- Geolocation from images (EXIF, landmark recognition, sun position)
- Username correlation across platforms
- Email pattern analysis and verification

**Specific Dork Patterns**:
```
site:pastebin.com "target"
site:github.com "target" + password
site:pdf "confidential" + "target"
inurl:admin + "target"
filetype:xls + "target" + email
intitle:"index of" + "target"
ext:sql + "target"
site:*.gov + "target"
```

## 2. SIGINT

**Definition**: Interception and analysis of signals and communications.

**In Investigative Context**:
- Email header analysis and routing path reconstruction
- Network traffic pattern analysis (from captured logs)
- Communication metadata analysis (who contacted whom, when, frequency)
- Encrypted traffic pattern recognition
- VoIP call detail records
- Message timestamp correlation across platforms
- Domain generation algorithm (DGA) detection
- Certificate and encryption artifact analysis

**Metadata Analysis Priorities**:
1. Sender/recipient patterns (temporal clustering, frequency)
2. Geographic routing (IP path, server locations)
3. Device fingerprints (User-Agent, client signatures)
4. Communication networks (community detection in contact graphs)

## 3. IMINT

**Definition**: Intelligence derived from visual imagery.

**Applications**:
- Geolocation verification from photographs
- Satellite imagery analysis (Google Earth, Sentinel, Planet)
- Building/location identification from visual cues
- Timeline reconstruction from image metadata
- Deepfake/manipulation detection (ELA, noise analysis, shadow consistency)
- License plate and vehicle identification
- Facial recognition cross-reference (open source tools)
- Object recognition and pattern matching
- Change detection across time-stamped imagery

**Verification Checklist**:
- [ ] EXIF data consistency with claimed location
- [ ] Shadow angles match claimed time
- [ ] Language on signs matches claimed location
- [ ] Architecture and vegetation match geography
- [ ] Weather records match sky conditions
- [ ] Sun position matches timestamp

## 4. GEOINT

**Definition**: Analysis of geographically referenced activities.

**Tools & Methods**:
- IP geolocation correlation
- Cell tower mapping and call detail record analysis
- GPS coordinate extraction and clustering
- Movement pattern analysis (timestamped locations)
- Geofencing and proximity analysis
- Spatial relationship mapping (entities near common locations)
- Satellite/aerial imagery timeline comparison
- OpenStreetMap intelligence (OSMINT)
- Marine/AIS tracking for vessel movements
- Flight tracking (ADS-B) for aircraft movements

## 5. MASINT

**Definition**: Intelligence from technical sensors measuring physical properties.

**Digital Applications**:
- File creation/modification timestamp analysis
- Hash analysis for file duplication detection
- Stylometric analysis (writing style fingerprinting)
- Device fingerprint correlation
- Linguistic pattern analysis (common phrases, grammar habits)
- Code authorship analysis (programming style)
- Cryptographic artifact analysis (key formats, implementation signatures)
- Network timing analysis (latency patterns, timezone inference)

## 6. SOCMINT

**Definition**: Intelligence from social media platforms.

**Platforms & Techniques**:
- Profile correlation across platforms (username, photo, bio matching)
- Network graph analysis (followers, following, mutual connections)
- Temporal activity pattern analysis (posting times = timezone inference)
- Content analysis (interests, affiliations, sentiment)
- Geotagged content mapping
- Deleted content recovery (archives, cached versions)
- Group/community membership analysis
- Event attendance and co-location
- Reaction/engagement pattern analysis
- Bot/inauthentic account detection

## 7. PsyOps

**Definition**: Psychological operations to influence behavior and reveal information.

**In Investigative Context** (defensive/analysis only):
- Narrative pattern analysis (who benefits, intended effect)
- Information operation detection (coordinated inauthentic behavior)
- Influence campaign mapping (bot networks, amplifier accounts)
- Deception detection in statements (linguistic indicators)
- Source credibility assessment
- Motivation analysis (why information is released, to what end)
- Disinformation pattern recognition (known tactics: distraction, doubt, division)

## 8. HUMINT Principles

**Digital Application**:
- Source reliability assessment (A-F grading)
- Information credibility evaluation (1-5 confidence)
- Motivation analysis (MICE: Money, Ideology, Coercion, Ego)
- Corroboration requirements (never single-source critical claims)
- Handling agent/source digital tradecraft analysis
- Communication pattern tradecraft assessment

## 9. Deductive Logic Framework

**Syllogistic Structure for Investigations**:
```
Major Premise: All members of group X exhibit pattern Y
Minor Premise: Subject Z exhibits pattern Y
Conclusion: Subject Z is associated with group X
(Confidence level: probable / highly likely / certain)
```

**Chain of Deduction Rules**:
1. Each deduction must be supported by verifiable evidence
2. Correlation does not imply causation - always seek mechanism
3. Apply Occam's Razor: simplest explanation that accounts for all facts
4. Test alternative hypotheses systematically
5. Confidence level must decrease with each inferential step
6. All assumptions must be explicitly stated
7. Contradictory evidence must be addressed, not ignored

**Bayesian Reasoning for Confidence Assessment**:
```
Posterior Probability = (Likelihood × Prior) / Evidence

For each claim, calculate:
- Prior probability (base rate)
- Evidence strength (supporting/contradicting)
- Updated confidence after each piece of evidence
- Final probability after all evidence considered
```

**Investigation Standards**:
- **Circumstantial**: Evidence requires inference to connect to conclusion
- **Direct**: Evidence proves fact without inference
- **Corroborated**: Multiple independent sources confirm
- **Hearsay**: Secondhand information, mark confidence lower
- **Exculpatory**: Evidence favorable to subject, must include

## 10. Intelligence Cycle

```
1. DIRECTION    → Define investigation scope, priorities, requirements
                     |
2. COLLECTION   → Gather data from all applicable sources
                     |
3. PROCESSING   → Normalize, structure, enrich raw data
                     |
4. ANALYSIS     → Apply intelligence disciplines, find patterns
                     |
5. PRODUCTION   → Create intelligence products (reports, briefs)
                     |
6. DISSEMINATION→ Deliver to stakeholders in actionable form
                     ↓
              (Feedback loop to Direction)
```

## 11. Analytical Techniques

**Pattern Analysis**:
- Link analysis (entity relationship mapping)
- Timeline/temporal analysis
- Event flow analysis
- Communication network analysis (centrality, betweenness, clusters)
- Financial flow analysis (follow the money)
- Spatial analysis (geographic clustering)

**Structured Analytical Techniques**:
- Analysis of Competing Hypotheses (ACH)
- Key Assumptions Check
- Indicators/Warning Sign development
- Devil's Advocacy (deliberate contrarian analysis)
- Team A/Team B analysis
- Red Team analysis
- Scenario generation
- Morphological analysis

**ACH (Analysis of Competing Hypotheses) Process**:
1. Identify all possible hypotheses (minimum 3)
2. List significant evidence and arguments for/against each
3. Prepare matrix: hypotheses vs. evidence
4. Refine matrix (delete evidence that all hypotheses explain)
5. Draw tentative conclusion about relative likelihood
6. Analyze sensitivity to critical evidence
7. Report conclusions and evidence gaps
