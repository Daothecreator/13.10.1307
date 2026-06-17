# Data Sources & Databases Reference

## Table of Contents
1. [Leaked Data & Breach Databases](#1-leaked-data--breach-databases)
2. [Dark Web & Underground Sources](#2-dark-web--underground-sources)
3. [Open Data & Transparency Portals](#3-open-data--transparency-portals)
4. [Relational Databases (SQL)](#4-relational-databases-sql)
5. [NoSQL Databases](#5-nosql-databases)
6. [Data Warehouses & Analytics](#6-data-warehouses--analytics)
7. [Stream Processing](#7-stream-processing)
8. [Vector Databases (AI/ML Search)](#8-vector-databases-aiml-search)
9. [Graph Databases](#9-graph-databases)
10. [Time-Series Databases](#10-time-series-databases)
11. [Cloud-Native & Specialized](#11-cloud-native--specialized)
12. [In-Memory & Caching](#12-in-memory--caching)

---

## 1. Leaked Data & Breach Databases

| Source | Type | Access | Notes |
|--------|------|--------|-------|
| DeHashed | Breach search engine | API / Web | 15B+ records from 500+ breaches; search by email, username, IP, name |
| LeakIX | Public-facing asset & leak exposure | API / Web | Indexes exposed services, leaks, misconfigurations |
| IntelligenceX (IntelX) | Deep/dark web search engine | API / Web | Archives dark web, leaks, documents, domains; historical snapshots |
| Distributed Denial of Secrets (DDoSecrets) | Leaked document archive | Torrent / Web | Whistleblower-provided datasets; journalists' primary source |
| Cryptome | Document archive | Web / FTP | Operating since 1996; hosts suppressed documents |
| OpenLeaks | Whistleblower platform | Web | Secure submission and analysis platform |
| Have I Been Pwned (HIBP) | Breach notification | API | Validate if email/phone appears in known breaches |
| Snusbase | Breach compilation | API / Web | Cross-referenced breach database |
| Leak-Lookup | Breach aggregator | API | Query across multiple breach databases |
| Vigilante.pw | Breach database directory | Web | Directory of known breach databases |

## 2. Dark Web & Underground Sources

| Source | Type | Access | Notes |
|--------|------|--------|-------|
| Dread | Dark web forum | Tor | Reddit-like forum for criminal discussions |
| 2b2t BBS / Related underground BBS | Textboard forums | Various | Historical and underground communications |
| Tor hidden services index | Onion sites | Tor | Various dark web marketplaces and forums |
| XSS.is | Exploit/hacker forum | Invite / Web | Russian-language cybercriminal forum |
| Exploit.in | Hacker forum | Invite / Web | Data sales, exploit trading |
| Nulled.to | Hacking community | Web | Leaks, tutorials, tools |
| RaidForums (historical) / successors | Forum archives | Mirrors | Historical breach data marketplace |
| BreachForums (historical) / successors | Forum archives | Mirrors | Successor breach trading platforms |

## 3. Open Data & Transparency Portals

| Source | Type | Access | Notes |
|--------|------|--------|-------|
| ICIJ Offshore Leaks Database | Financial transparency | Web / Bulk | Offshore financial records, shell companies, UBOs |
| OCCRP Aleph | Investigative data platform | Web / API | Entity graph of persons, companies, assets globally |
| OpenCorporates | Company registry | API | 200M+ companies from 140+ jurisdictions |
| OpenOwnership | Beneficial ownership | API / Bulk | UBO registers worldwide |
| USAspending.gov | US government spending | API / Bulk | Federal contract and grant data |
| EU Transparency Register | Lobbying register | Web | EU interest representation |
| UK Companies House | Company registry | API | UK corporate filings |
| EDGAR (SEC) | US securities filings | API / FTP | 10-K, 10-Q, insider trading |
| Panama Papers (ICIJ) | Leaked documents | Web | Historical offshore leak data |
| Paradise Papers (ICIJ) | Leaked documents | Web | Offshore financial records |
| Pandora Papers (ICIJ) | Leaked documents | Web | Latest major offshore leak |
| FinCEN Files (ICIJ) | SARs database | Web | Suspicious activity reports |

## 4. Relational Databases (SQL)

| Database | Best For | Key Features |
|----------|----------|--------------|
| PostgreSQL | Complex queries, geospatial, JSON | PostGIS, full-text search, window functions |
| MySQL / MariaDB | Web applications, LAMP stack | High compatibility, replication |
| SQLite | Embedded, mobile, local analysis | Serverless, single-file, zero-config |
| Oracle DB | Enterprise workloads | RAC, advanced security, partitioning |
| IBM Db2 | Enterprise, hybrid cloud | AI-integrated, column-organized tables |
| Microsoft SQL Server | Enterprise Windows environments | T-SQL, SSIS, comprehensive tooling |
| Amazon Aurora | Cloud-native relational | MySQL/PostgreSQL compatible, auto-scaling |
| Cloud SQL (GCP) | Managed PostgreSQL/MySQL | Auto-backups, replication |
| SingleStore | HTAP (OLTP + OLAP) | In-memory + disk columnstore |
| TiDB | Distributed SQL | Horizontal scaling, MySQL compatible |
| CockroachDB | Distributed SQL | Survival goals (node/region/cloud) |
| DuckDB | Analytical embedded | In-process, zero external dependencies |

## 5. NoSQL Databases

| Database | Type | Best For |
|----------|------|----------|
| MongoDB | Document store | Flexible schema, JSON documents |
| Amazon DynamoDB | Key-value / Document | Serverless, single-digit ms latency |
| Azure Cosmos DB | Multi-model | Global distribution, multiple APIs |
| Couchbase | Document / Key-value | Mobile sync, edge computing |
| Cassandra / ScyllaDB | Wide-column | Write-heavy, time-series, high availability |
| HBase | Wide-column | BigTable model, Hadoop ecosystem |

## 6. Data Warehouses & Analytics

| Platform | Architecture | Key Strengths |
|----------|-------------|---------------|
| Snowflake | Cloud-native, separated compute/storage | Zero-copy cloning, time travel, data sharing |
| Google BigQuery | Serverless, columnar | Petabyte-scale, ML integration (BQML) |
| Amazon Redshift | Columnar MPP | Spectrum (query S3), concurrency scaling |
| Databricks | Lakehouse (Delta Lake) | Spark-based, MLflow, Unity Catalog |
| ClickHouse | Columnar OLAP | Real-time analytics, vectorized execution |
| Apache Druid | Real-time analytics | Streaming ingestion, sub-second queries |
| Teradata | Enterprise MPP | Massive scale, workload management |
| Starburst Galaxy | Trino-based | Federated queries across data sources |

## 7. Stream Processing

| Platform | Model | Use Cases |
|----------|-------|-----------|
| Apache Kafka | Distributed log | Event streaming, real-time pipelines |
| Apache Flink | Stream processing | Stateful computations, exactly-once |
| Apache Spark Streaming | Micro-batch | Integration with Spark ecosystem |
| ksqlDB / Flink SQL | SQL on streams | Stream analytics without code |
| Redpanda | Kafka-compatible | Simpler ops, C++ implementation |
| Apache Pulsar | Tiered storage | Unified queuing and streaming |

## 8. Vector Databases (AI/ML Search)

| Database | Index Types | Best For |
|----------|-------------|----------|
| Pinecone | Managed, proprietary | Production AI, metadata filtering |
| Milvus | IVF, HNSW, ANNOY | Billion-scale vectors, hybrid search |
| Weaviate | HNSW | Graph+vector hybrid, modular AI |
| Qdrant | HNSW | Filterable vector search, Rust-based |
| Elasticsearch | kNN, dense_vector | Text + vector hybrid search |
| pgvector (PostgreSQL) | ivfflat, hnsw | SQL-native vector operations |
| Faiss (Meta) | IVF, PQ, HNSW | Research, in-memory GPU acceleration |
| LanceDB | Disk-based vector | Serverless embeddings, multi-modal |
| Chroma | Simple embedding store | Rapid prototyping, LangChain integration |
| Vespa | Hybrid | Real-time indexing, tensor operations |

## 9. Graph Databases

| Database | Query Language | Best For |
|----------|---------------|----------|
| Neo4j | Cypher | Property graphs, fraud detection, recommendations |
| Amazon Neptune | Gremlin / SPARQL | Knowledge graphs, RDF + property |
| TigerGraph | GSQL | Native parallel graph, deep link analysis |
| ArangoDB | AQL | Multi-model (graph + document + KV) |
| JanusGraph | Gremlin | Distributed graph, Titan successor |
| Dgraph | GraphQL+- | Horizontal scaling, native distributed |

## 10. Time-Series Databases

| Database | Storage Model | Best For |
|----------|--------------|----------|
| TimescaleDB | SQL (PostgreSQL extension) | SQL-native time-series, continuous aggregation |
| InfluxDB | TSM / Parquet | Metrics, IoT, monitoring |
| Apache Pinot | Columnar | Real-time OLAP, user-facing analytics |
| QuestDB | Relational columnar | Fast SQL time-series, JOINs |
| TDengine | Purpose-built | IoT-optimized, edge-cloud sync |

## 11. Cloud-Native & Specialized

| Database | Specialty | Notes |
|----------|-----------|-------|
| Amazon Neptune ML | Graph + ML | Graph neural network predictions |
| BigQuery ML | SQL ML | Train models with SQL |
| Snowpark | UDFs in Python/JS | In-warehouse computation |
| Firebolt | Extreme ingestion | F3 format (sorted+encoded) |
| Exasol | In-memory analytics | TPC-DS performance leader |
| VoltDB | Fast transactions | ACID at scale, telco/finance |
| Apache Ignite | In-memory computing | Distributed cache + compute |

## 12. In-Memory & Caching

| Database | Type | Best For |
|----------|------|----------|
| Redis | Key-value, data structures | Caching, sessions, pub/sub, streams |
| Memcached | Simple key-value | Lightweight caching |
| Hazelcast | IMDG | Distributed computing, caching |
| Tarantool | Lua + persistence | Real-time applications |

## Data Extraction Strategy

For each investigation topic, execute searches across source tiers in this priority:

1. **Tier 1 - Direct Identity**: DeHashed, LeakIX, IntelX, HIBP - search by person/entity identifiers (email, phone, username, IP, name)
2. **Tier 2 - Document Archives**: DDoSecrets, Cryptome, ICIJ databases, OCCRP Aleph - search by entity name, jurisdiction, associated persons
3. **Tier 3 - Corporate & Financial**: OpenCorporates, OpenOwnership, ICIJ Offshore Leaks, EDGAR - trace corporate structures, beneficial ownership
4. **Tier 4 - Dark Web**: Dread, XSS.is, Tor indexes - monitor for sale of related data, criminal discussions
5. **Tier 5 - Technical Infrastructure**: Shodan, Censys, certificate transparency logs - map digital infrastructure
6. **Tier 6 - Open Sources**: News archives, court records, social media, academic papers

All extracted data MUST be saved as structured CSV with consistent schemas:
- `source` - Origin database/platform
- `timestamp` - When data was collected/published
- `relevance_score` - 1-10 assessment of relevance to investigation topic
- `raw_data` - Complete extracted record
- `category` - Classification (identity, financial, communication, technical, relational)
- `confidence` - verified / probable / unverified
- `chain_of_custody` - Extraction method and timestamp
