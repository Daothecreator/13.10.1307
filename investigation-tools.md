# Investigation Tools & Platforms Reference

## Table of Contents
1. [OCCRP Aleph](#1-occrp-aleph)
2. [Bellingcat Online Investigation Toolkit](#2-bellingcat-toolkit)
3. [Google Dorks](#3-google-dorks)
4. [Shodan](#4-shodan)
5. [Censys](#5-censys)
6. [WhatBreach](#6-whatbreach)
7. [Cellebrite / MSAB](#7-cellebrite-msab)
8. [Specialized Search Engines](#8-specialized-search-engines)
9. [Network Analysis Tools](#9-network-analysis-tools)
10. [Document Analysis](#10-document-analysis)
11. [Social Media Investigation](#11-social-media-investigation)
12. [Financial Tracing](#12-financial-tracing)

---

## 1. OCCRP Aleph

**Type**: Investigative data platform / Entity graph
**URL**: https://aleph.occrp.org

**Capabilities**:
- Global database of persons, companies, assets, court cases, leaks
- Cross-referencing across datasets (Panama Papers, property records, sanctions lists)
- Entity resolution (same person across different datasets)
- Network graph visualization
- Document text extraction and search
- Alert system for new matches

**Search Operators**:
```
name:"Entity Name"
company:"Company Name"
schema:Person
schema:Company
schema:LegalEntity
countries:us
features:sanctioned
features:pep (politically exposed person)
```

**Investigative Workflow**:
1. Search target entity by name
2. Review associated entities (officers, addresses, subsidiaries)
3. Follow ownership chains (who owns what, through what)
4. Cross-reference with sanctions and PEP lists
5. Check property and vessel ownership
6. Download entity graph for offline analysis

## 2. Bellingcat Online Investigation Toolkit

**Type**: Open source investigative methodology + tools
**URL**: https://www.bellingcat.com

**Core Techniques**:
- **Geolocation**: Verify locations from visual media
- **Chronolocation**: Verify dates/times from visual cues
- **Social media verification**: Authenticate accounts and content
- **Satellite imagery analysis**: Compare ground photos with satellite
- **Flight tracking**: Track aircraft movements
- **Vessel tracking**: Maritime AIS tracking
- **Weapon/traffic analysis**: Identify munitions, vehicles

**Key Tools Referenced**:
- Google Earth Pro (historical imagery)
- Sentinel Hub / EO Browser (satellite)
- SunCalc.org (shadow angle calculation)
- InVID (video verification)
- Flightradar24 / ADS-B Exchange
- MarineTraffic / VesselFinder
- Forensically (image forensics)
- RevEye (reverse image search)
- Wayback Machine
- OpenStreetMap

## 3. Google Dorks

**Base URL**: https://www.google.com/search?q=

**Investigative Dorks Categories**:

**Document Discovery**:
```
site:drive.google.com "target" + confidential
site:docs.google.com "target"
site:scribd.com "target"
filetype:pdf + "target" + "internal"
filetype:doc + "target" + "password"
filetype:xls + "target" + "email"
filetype:csv + "target"
filetype:sql + "target"
filetype:env + "target"
filetype:log + "target"
```

**Configuration/Secrets Exposure**:
```
intitle:"index of" + "config"
intitle:"index of" + "backup"
intitle:"index of" + ".git"
intitle:"index of" + "database"
ext:sql + "target" + dump
ext:bak + "target"
ext:old + "target"
ext:swp + "target"
inurl:env + "target"
inurl:config + "target" + "password"
```

**Person/Identity**:
```
"email" + "target" + filetype:csv
"username" + "target" + site:pastebin.com
"target" + phone + filetype:pdf
"target" + "SSN" + filetype:xls
"target" + "passport"
```

**Network Infrastructure**:
```
site:shodan.io + "target"
site:censys.io + "target"
"target" + "IP address" + "server"
intitle:"dashboard" + "target"
```

## 4. Shodan

**Type**: IoT and internet device search engine
**URL**: https://www.shodan.io

**Search Operators**:
```
hostname:"target.com"
net:"1.2.3.0/24"
port:3389
product:"Microsoft Remote Desktop"
os:"Windows"
city:"Moscow"
org:"Target Organization"
ssl:"target.com"
http.title:"Dashboard"
vuln:CVE-2021-44228
```

**Investigative Applications**:
- Map attack surface of target infrastructure
- Identify exposed services and misconfigurations
- Track historical changes (Shodan Monitor)
- Certificate transparency search
- Discover related IP ranges and ASN
- Identify vulnerable services

## 5. Censys

**Type**: Internet asset discovery and monitoring
**URL**: https://search.censys.io

**Search Language**:
```
services.http.response.html_title: "Target"
services.port: 443
services.software.product: "nginx"
services.certificate.names: "target.com"
 autonomous_system.name: "Target ISP"
location.country_code: US
```

**Key Differentiators from Shodan**:
- Certificate-based search (find all certs for domain)
- Host ↔ Service relationship mapping
- More structured data model
- Historical certificate data

## 6. WhatBreach

**Type**: Data breach lookup tool
**URL**: https://whatbreach.com

**Use Cases**:
- Query if email/username appears in known breaches
- Retrieve breach details (date, compromised fields)
- Cross-reference with Have I Been Pwned
- Bulk breach checking for investigation targets

## 7. Cellebrite / MSAB

**Type**: Digital forensics platforms (reference only)
**Note**: Physical access to hardware required; referenced for forensic methodology standards.

**Capabilities (Methodology Reference)**:
- Mobile device extraction (logical, file system, physical)
- Cloud data extraction
- Application data parsing (WhatsApp, Signal, Telegram)
- Timeline analysis
- Cross-device correlation
- Report generation with chain of custody

**Forensic Principles Applied**:
- Bit-for-bit imaging before analysis
- Write-blocking to prevent modification
- Hash verification (MD5/SHA-256) of evidence integrity
- Chain of custody documentation
- Repeatable processes for court admissibility

## 8. Specialized Search Engines

| Engine | Purpose | URL |
|--------|---------|-----|
| IntelligenceX | Deep/dark web search | intelx.io |
| Spyse | Internet asset registry | spyse.com |
| BinaryEdge | Attack surface discovery | binaryedge.io |
| Fofa | Chinese asset search engine | fofa.info |
| Hunter.io | Email finder and verifier | hunter.io |
| Phonebook.cz | Email/username/domain search | phonebook.cz |
| WhatsMyName | Username enumeration | whatsmyname.app |
| Namechk | Username availability check | namechk.com |
| Sherlock | Username search across 400+ sites | github.com/sherlock-project |
| Maltego | Link analysis and visualization | maltego.com |
| theHarvester | Subdomain/email harvesting | github.com/laramies/theHarvester |
| Amass | DNS enumeration and mapping | github.com/OWASP/Amass |

## 9. Network Analysis Tools

| Tool | Function |
|------|----------|
| Wireshark (methodology) | Packet capture and analysis |
| Nmap (methodology) | Network scanning and service detection |
| Masscan | Internet-scale port scanning |
| SSL Labs | SSL/TLS configuration analysis |
| URLScan.io | Website sandbox analysis |
| VirusTotal | File/URL/IP reputation |
| AbuseIPDB | IP reputation and abuse reports |
| BGP.he.net | BGP routing and ASN analysis |

## 10. Document Analysis

| Tool | Purpose |
|------|---------|
| ExifTool | Metadata extraction from files |
| pdfinfo | PDF metadata and structure |
| strings | Extract text strings from binaries |
| binwalk | File carving and embedded file extraction |
| Foremost | File recovery and carving |
| DocumentCloud | Document publishing and annotation |
| Tabula | Extract tables from PDFs |

## 11. Social Media Investigation

| Platform | Key Investigative Features |
|----------|---------------------------|
| Twitter/X | Advanced search, account history, follower analysis |
| Facebook | Graph search remnants, profile correlation |
| LinkedIn | Professional network mapping, company affiliation |
| Instagram | Geotagged posts, story archives, follower overlap |
| Telegram | Channel analysis, bot activity |
| VKontakte | Russian-language social network |
| Reddit | Subreddit participation, post history |
| TikTok | Video metadata, account connections |
| Discord | Server membership, message history |

## 12. Financial Tracing

| Tool/Source | Purpose |
|-------------|---------|
| ICIJ Offshore Leaks | Offshore financial structures |
| OpenCorporates | Corporate registry search |
| OpenOwnership | Beneficial ownership |
| OCCRP Aleph | Cross-border financial connections |
| Blockchain.com / Etherscan | Cryptocurrency transaction tracing |
| Chainalysis (methodology) | Crypto forensic analysis |
| CourtListener | US court cases and dockets |
| PACER | Federal court records |
| OpenSecrets | Political donations and lobbying |
| ProPublica Nonprofit Explorer | US nonprofit financials |
