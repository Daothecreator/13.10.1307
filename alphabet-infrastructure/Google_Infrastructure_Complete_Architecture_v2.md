# GOOGLE INFRASTRUCTURE: COMPLETE ARCHITECTURAL MAP

## Integrated Systems Analysis — Production Stack

### v2.0 | | 2026-07-23

\---

## PREAMBLE

This document maps Google's production infrastructure as a cohesive, layered organism. Every design decision at one stratum constrains the design space of all strata above and below. Dependencies are the spine of this analysis. No component exists in isolation.

**Core axiom**: At Google's scale, the dominant failure mode is not component failure, but cascading failure through hidden dependencies.

\---

## LAYER 0: PHYSICAL SUBSTRATE

### Foundation of All Computation

### 0.1 Data Center Infrastructure

Google operates warehouse-scale computers — building-scale distributed systems consisting of row after row of homogeneous servers and storage. The aggregate bandwidth of a single Google datacenter exceeds that of the entire public Internet.

* **Power delivery**: N+2 redundancy, 480V DC distribution, battery + diesel backup
* **Cooling systems**: Free cooling (evaporative + outside air), hot aisle containment, liquid cooling for accelerators
* **Server hardware**: Custom motherboards, homogeneous fleet for replaceability
* **Rack topology**: 40-80 servers per rack, top-of-rack (ToR) switch

**Design constraint**: Physical homogeneity enables software-defined everything. If every server is identical, scheduling and failure recovery become purely software problems.

### 0.2 NIC / Storage / Interconnect

* **NIC**: Custom TPU/CPU-attached, RDMA-capable, kernel bypass
* **Storage**: NVMe SSD local + Colossus distributed
* **Interconnect**: Custom optical links between buildings, DWDM fiber between campuses

\---

## LAYER 1: NETWORK FABRIC

### The Nervous System

### 1.1 Five Generations of Datacenter Networks

Google's datacenter network evolved through five generations, each building on the previous:

|Generation|Year|Key Innovation|Scale|
|-|-|-|-|
|Firehose 1.0|2005|First Clos fabric|2K servers|
|Firehose 1.1|2006|Custom switch|8K servers|
|Watchtower|2008|10G merchant silicon|50K+ servers|
|Saturn|2012|40G, virtual chassis|100K+ servers|
|Jupiter|2015+|1.3 Pbps, SDN control|Building-scale|

Source: Jupiter Rising, SIGCOMM 2015

### 1.2 Clos Fabric Topology

Jupiter uses a 3-stage Clos topology:

```
        SPINE LAYER (L3)
    S1 ------ S2 ------ S3
     |        |         |
    F1 ------ F2 ------ F3     (Fabric/Aggregation)
     |        |         |
    ToR\_A   ToR\_B   ToR\_C
     |        |         |
  \[Servers] \[Servers] \[Servers]
```

* **ToR**: 48x10G down to servers, 16x10G up to fabric
* **Fabric block**: 2-stage Clos of 16x16x40G chips, 256x10G to ToRs, 64x40G to spines
* **Spine**: 2-stage Clos of 6 basic units, 128x40G to aggregation blocks
* **Final cluster**: 256 spine switches, 64 aggregation blocks, 32 ToRs per block = 2,048 racks
* **Oversubscription**: 3:1 at ToR layer

Source: Jupiter Rising, SIGCOMM 2015

### 1.3 Jupiter Network — Centralized Control

Three themes unify Jupiter's design:

1. **Multi-stage Clos topologies** built from commodity switch silicon support cost-effective deployment of building-scale networks
2. **Centralized control mechanism** based on global configuration pushed to all datacenter switches replaces complex decentralized routing protocols
3. **Modular hardware design** coupled with simple, robust software supports inter-cluster and wide-area networks

**Scale**: Runs at dozens of sites across the planet, scaling in capacity by 100x over ten years to more than 1 Pbps of bisection bandwidth per datacenter.

Source: Jupiter Rising, SIGCOMM 2015

### 1.4 Jupiter Evolving — Direct-Connect Topology (SIGCOMM 2022)

Jupiter evolved from standard Clos to a **direct-connect topology** using:

* MEMS-based Optical Circuit Switches
* Software-Defined Networking
* Automated Safe Operation

This enables dynamic traffic and topology engineering for observed block-level traffic patterns, achieving comparable throughput and shorter paths relative to conventional Clos, with substantial Capex and Opex savings.

Source: Jupiter Evolving, SIGCOMM 2022

### 1.5 SDN Control Plane

* **Consistency model**: Eventually consistent for forwarding state, strongly consistent for policy
* **Failure mode**: Controller partition -> switches continue with last-known-good state
* **Control reachability**: Multiple independent domains per site, connected only through dataplane. Each domain uses Paxos quorum-based master election.

Source: Lessons Learned from B4, USENIX ATC 2015

### 1.6 B4 — Software-Defined WAN

B4 is Google's private WAN connecting datacenters across the planet.

**Unique characteristics**:

* Massive bandwidth requirements deployed to a modest number of sites
* Elastic traffic demand that seeks to maximize average bandwidth
* Full control over edge servers and network, enabling rate limiting and demand measurement

**Architecture**:

* Hierarchical SDN: local SDN control at each site + global centralized traffic engineering
* Site controller: OpenFlow controller (Orion) + Quagga for BGP/IS-IS + TE Agent
* TE abstraction: Each site is a single node with a single edge of given capacity to each remote site
* Tunnels: IP-in-IP encapsulation for site-level paths
* **Result**: Centralized TE delivered up to 30% additional throughput; many WAN links run at near 100% utilization

Source: B4: Experience with a Globally-Deployed Software Defined WAN, SIGCOMM 2013

### 1.7 Bandwidth Enforcer (BwE)

BwE is a global, hierarchical bandwidth allocation infrastructure for WAN distributed computing.

**Key insight**: Individual flows with fixed priority are not the ideal basis for bandwidth allocation. A service may have highest priority to receive 10 Gb/s, but upon reaching that allocation, incremental priority drops sharply, favoring allocation to other services.

**BwE supports**:

* Service-level bandwidth allocation following prioritized bandwidth functions
* Independent allocation and delegation policies according to user-defined hierarchy
* Multi-path forwarding common in traffic-engineered networks
* Central administrative point to override policy during exceptional conditions

**Production result**: BwE has delivered more service-efficient bandwidth utilization and simpler management for multiple years.

Source: BwE: Flexible, Hierarchical Bandwidth Allocation, SIGCOMM 2015

### 1.8 Freedome — Campus-Level Interconnect

Freedome is Google's campus-level interconnect network, complementing Jupiter (within datacenter) and Andromeda (cloud virtualization). It connects multiple datacenter buildings within a campus.

Source: Amin Vahdat keynote, Open Networking Summit 2015

### 1.9 Andromeda — Cloud Network Virtualization

Andromeda is Google Cloud Platform's network virtualization stack.

**Requirements**:

* Performance isolation among customer virtual networks
* Scalability to 100,000+ VMs
* Rapid provisioning (tens of thousands of VMs in seconds)
* Bandwidth and latency largely indistinguishable from underlying hardware
* High feature velocity combined with high availability

**Architecture**:

* **Flow Processing Hierarchy**: Flows dynamically assigned to programming paths based on requirements
* **Hoverboard Model**: Gateways handle long tail of low-bandwidth flows; control plane programs direct host-to-host offload flows for high-bandwidth traffic
* **On-Host Dataplane**: OS-bypass busy-polling userspace dataplane
* **Coprocessor Path**: CPU-intensive operations (firewall, NAT, load balancing) on separate threads

**Evolution**:

* Andromeda 1.0: Kernel datapath + modified Open vSwitch
* Andromeda 2.0: OS-bypass userspace dataplane
* Andromeda 2.1: Direct VM virtual NIC ring access, bypassing VMM
* Andromeda 2.2: Intel QuickData DMA engines for larger packet copies

**Performance**: 32.8 Gb/s using a single core; 300ns per-packet CPU budget for Fast Path.

**Scaling result**: With Hoverboard model, programming 1.5M flows for 40K VMs takes 1.9 seconds. Under preprogrammed model, 487M flows take 74 seconds and cause stability issues.

Source: Andromeda: Performance, Isolation, and Velocity at Scale, NSDI 2018

### 1.10 Load Balancing: Maglev

Maglev is Google's software-based network load balancer running on commodity Linux servers.

**Key properties**:

* Distributed software system (not hardware appliance)
* Capacity adjusted by adding/removing servers
* ECMP from routers distributes packets evenly to Maglev machines
* Consistent hashing + connection tracking for fault tolerance
* Direct Server Return (DSR) — backend responses bypass Maglev
* **Performance**: Single Maglev machine saturates 10 Gbps link with small packets
* **Production**: Serving Google's traffic since 2008; also provides load balancing for Google Cloud Platform

Source: Maglev: A Fast and Reliable Software Network Load Balancer, NSDI 2016

### 1.11 Anycast Routing

* Same IP announced from multiple PoPs via BGP
* Selection: Closest by latency or least-loaded
* Use cases: DNS, GFE (Google Front End), CDN

### 1.12 GSLB (Global Server Load Balancing)

* Geographic traffic distribution
* Inputs: Server load, health, capacity, user proximity
* DNS-based: Returns different A/AAAA records per region
* HTTP-based: 302 redirects for finer control

### 1.13 BGP Edge

* Two separate backbones: B2 (Internet-facing traffic) and B4 (inter-datacenter traffic)
* B4 carries more traffic than B2 and has higher growth rate
* Peering: Private + public IX + transit
* Route filtering: IRR + RPKI for prefix validation

Source: Lessons Learned from B4, USENIX ATC 2015

### 1.14 GFE — Google Front End

GFE is the reverse-proxy frontend service that terminates all incoming user traffic.

**Function**:

* Accepts incoming HTTP(S) requests
* Handles TLS handshakes and SSL termination
* Enforces load balancing
* Redirects traffic to optimal backend
* Protects from DDoS attacks
* Distributed across hundreds of global locations

**Request flow**: DNS -> Anycast IP -> GFE -> TLS termination -> GSLB -> Backend service

Source: SRE Book, Production Environment chapter

\---

## LAYER 2: CONTROL PLANE

### The Brain

### 2.1 Borg — Cluster Manager

Borg is Google's cluster management system, the precursor to Kubernetes.

**Architecture**:

* **Borgmaster**: Logical node, replicated via Paxos for high availability. Maintains cluster state in distributed persistent storage.
* **Borglet**: Agent on each machine. Starts/stops tasks, manages physical resources, reports status.
* **Scheduler**: Independent service, asynchronously handles task scheduling using Borgmaster state.

**Scheduling**:

* Two-pass scheduler: First pass finds feasible placement quickly; second pass optimizes for utilization and fragmentation
* Priority-based: Higher-priority jobs (production) preempt lower-priority (batch)
* Resource tracking: CPU, memory, disk, network

**Workloads**:

* **Production**: Latency-sensitive (Search, Gmail), guaranteed resources, higher priority
* **Batch**: Analytics, MapReduce, use leftover capacity, preemptable

**Scale**: Tens of thousands of machines, millions of tasks.

**Containers**: Lightweight process-level containers (precursor to Docker) for resource isolation.

Source: Large-scale Cluster Management at Google with Borg, EuroSys 2015

### 2.2 Configuration Management

* **System**: Borgcfg + Protobuf configs
* **Distribution**: Chubby-backed consistent store
* **Validation**: Type-checked, dependency-resolved before push

\---

## LAYER 3: COORDINATION LAYER

### The Skeletal System

### 3.1 Chubby — Distributed Lock Service

Chubby is a distributed lock service + small-file storage.

**API**: POSIX-like (open, close, read, write, acquire lock)
**Consistency**: Linearizable for locks, sequential for file reads
**Scale**: Tens of thousands of clients per instance
**Use cases**: Leader election, configuration storage, service discovery

**Critical dependency**: Chubby is the keystone of the entire stack. Failure propagates to Borg (scheduling stops), SDN (controller election fails), Spanner (timestamp oracle unavailable), Zanzibar (policy evaluation stalls). Running systems continue with cached state.

Source: The Chubby Lock Service for Loosely-Coupled Distributed Systems, OSDI 2006

### 3.2 Paxos — Consensus Layer

Multi-Paxos is used for replicated state machines across Google infrastructure.

**Pattern**: All replicas start from same state, apply same operations in same order -> deterministic identical final state.
**Application**: Chubby, Spanner, F1, Borgmaster.

### 3.3 Leader Election

* Via Chubby: Ephemeral locks on well-known files
* Failover: \~10-30 seconds (Chubby session timeout)
* Split-brain prevention: Chubby lock = single source of truth

### 3.4 Membership Service

* Gossip protocol + Chubby-backed authoritative list
* Eventual consistency for gossip, strong for Chubby

### 3.5 Quorum System

* Majority quorums: 2f+1 tolerates f failures
* Geo-distributed: Quorums span regions for disaster tolerance

### 3.6 State Reconciliation

* Trigger: Network partition heals, replica rejoins
* Mechanism: Merkle trees for efficient diff, then replay missing operations

\---

## LAYER 4: TIME LAYER

### The Metronome

### 4.1 TrueTime API

TrueTime provides globally consistent timestamps using GPS + atomic clocks.

```
TTinterval: \[earliest, latest]  // Interval, not point
TT.now(): returns current TTinterval
TT.after(t): sleep until t.latest
TT.before(t): true if t.latest < now.earliest

Uncertainty bound epsilon: typically 1-7ms (can be 100ms+ under load)
```

**Guarantee**: If event A happens before B, TT(A) < TT(B) with high probability.

**Critical dependency**: Without TrueTime, Spanner would require global locks or synchronous replication for all transactions, making it unusable at scale.

Source: Spanner: Google's Globally-Distributed Database, OSDI 2012

\---

## LAYER 5: STORAGE CONSISTENCY LAYER

### The Transaction Engine

### 5.1 Two-Phase Commit (2PC)

Spanner uses 2PC for distributed transactions across Paxos groups.

**Phase 1 (PREPARE)**: Coordinator sends PREPARE to participants; participants vote YES/NO.
**Phase 2 (COMMIT/ABORT)**: If all YES, coordinator sends COMMIT; if any NO, sends ABORT.
**Logging**: Coordinator logs decision before sending COMMIT; participants log prepare before voting YES.

### 5.2 Paxos Group

* Unit of replication: 3-5 replicas per group
* Leader: Handles all writes, coordinates reads
* Followers: Apply log, serve stale reads
* Reconfiguration: Membership changes via Paxos itself

### 5.3 Serializable Transactions via TrueTime

* **Mechanism**: Commit wait — sleep until TT.now().latest > commit timestamp
* **Cost**: Adds \~2\*epsilon latency (typically 4-14ms)
* **Result**: External consistency — commit order matches real-time order

Source: Spanner: Google's Globally-Distributed Database, OSDI 2012

### 5.4 Write-Ahead Log (WAL)

* Log before applying to state machine
* Archived to Colossus, compacted periodically

### 5.5 Replication Manager

* Placement goals: Geographic diversity, load balance, failure domain isolation
* Repair: Detect missing/corrupt replicas, rebuild from healthy ones

\---

## LAYER 6: DATA SUBSTRATE

### The Memory

### 6.1 Spanner

**Data Model**:

* Hierarchical: DATABASE -> TABLE -> ROW -> COLUMN
* Interleaved tables: Child rows stored with parent for locality
* Schemas: SQL-like, strongly typed (GoogleSQL dialect)

**Query Semantics**:

* Full SQL (joins, subqueries, aggregations)
* Transactions: ACID, distributed, externally consistent
* Reads: Strong (current), bounded staleness, exact staleness

**Internal Architecture**:

* **Universe**: Global scope
* **Regions**: Geographic divisions (US-E1, EU-W1)
* **Zones**: Deployment units within regions
* **Paxos Groups**: 3-5 replicas per group, leader-based writes
* **Directories**: Data placement units, moved between Paxos groups for load balancing

**Storage Layer**:

* Bottom: Colossus (distributed file system)
* Middle: Paxos state machine (replicated log)
* Top: Tablet (shard of data, \~100MB-1GB)

**TrueTime Integration**: Transaction timestamps assigned by Paxos leader; commit wait ensures external consistency.

Source: Spanner: Google's Globally-Distributed Database, OSDI 2012

### 6.2 Bigtable

**Data Model**:

* Sparse, distributed, persistent multidimensional sorted map
* (row:string, column:string, time:int64) -> string
* Column families: Grouped columns with shared properties

**Query Semantics**:

* Direct API (Get, Put, Scan, Delete) — no SQL
* Single-row transactions only
* No joins, no secondary indexes natively

**Internal Architecture**:

* **Master**: Manages tablet assignment, handles schema changes, rebalances load
* **Tablet Server**: Serves data for a set of tablets
* **Tablet**: Range of rows, \~100-200MB
* **Storage**: SSTables in Colossus, MemTable in memory
* **Compaction**: Periodic merge of SSTables

Source: Bigtable: A Distributed Storage System for Structured Data, OSDI 2006

### 6.3 Colossus (GFS2)

**Evolution**: GFS (2003) -> Colossus (2010+)

**Architecture**:

* **Master**: Manages metadata (file -> chunk mapping), not data path. Replicated via Chubby.
* **Chunk Server**: Stores 64MB chunks. Replication: 3x default, erasure coding for cold data.
* **Client**: Directly reads/writes chunks from chunkservers.

**Key differences from GFS**:

* Chunk size: 64MB (vs 64KB in GFS)
* Multiple masters for scalability
* Erasure coding for cold data

Source: The Google File System, SOSP 2003 (GFS); Colossus details from internal evolution

### 6.4 F1

F1 is a distributed SQL database built on Spanner.

**Data Model**:

* Built on Spanner (inherits all Spanner guarantees)
* SQL interface with hierarchical schema
* Supports: secondary indexes, foreign keys, cascades

**Query Semantics**:

* Full SQL (joins, subqueries, aggregations)
* Transactions: ACID, distributed
* Asynchronous schema changes

**Internal Architecture**:

* SQL layer: Query parsing, optimization, execution
* Storage: Spanner
* Protocol: Stubby (gRPC predecessor) for client communication

Source: F1: A Distributed SQL Database That Scales, VLDB 2012

\---

## LAYER 7: COMMUNICATION LAYER

### The Circulatory System

### 7.1 Stubby — Internal RPC Framework

Stubby is Google's general-purpose RPC infrastructure, internal predecessor to gRPC.

**Properties**:

* Developed \~2001 for internal use
* Manages billions of communication requests per second
* Built around Protocol Buffers for serialization
* Used for all inter-process communication within and across datacenters
* Language bindings in C++ and Java

**Evolution**: Stubby (internal, \~2001) -> gRPC (open source, 2015)

gRPC differences from Stubby:

* Built on HTTP/2 (allows streaming)
* Open source
* Supports 4 API types: unary, server-streaming, client-streaming, bidirectional-streaming

Source: gRPC documentation; Google internal engineering blogs

### 7.2 Protocol Buffers

Protocol Buffers are Google's language-neutral, platform-neutral serialization format.

**Properties**:

* Schema defined in .proto files
* Binary serialization — more compact than JSON/XML
* Backward and forward compatibility
* Most commonly-used data format at Google
* Used extensively in inter-server communications and archival storage

**Versions**:

* Proto1: Internal use only
* Proto2: Open sourced 2008
* Proto3: Released 2016, removed required fields, simplified

Source: Protocol Buffers Documentation (protobuf.dev)

\---

## LAYER 8: POLICY AND AUTHORIZATION LAYER

### The Immune System

### 8.1 Zanzibar — Global Authorization System

Zanzibar is Google's consistent, global authorization system.

**Core Abstractions**:

* **Tuple**: (object, relation, user, \[zookie])

  * object: namespace:id (e.g., "doc:readme")
  * relation: string (e.g., "owner", "editor", "viewer")
  * user: user:id or userset:namespace:id#relation
* **Permission**: Computed relation via union/intersection/exclusion

**Example tuples**:
(doc:readme, owner, user:alice)
(doc:readme, viewer, userset:group:eng#member)
(group:eng, member, user:bob)

**Consistency Guarantees**:

* **Zookies**: Consistency tokens carried by clients
* **Read-your-writes**: Writes visible to subsequent reads
* **Snapshot reads**: Read at specific snapshot timestamp
* **Bounded staleness**: Read within X seconds of now

**Authorization Enforcement Points**:

|Point|Layer|Mechanism|Freshness|
|-|-|-|-|
|1|Ingress (GFE)|OAuth token validation|Per-request|
|2|Service|Zanzibar RPC|Cached (5-60s)|
|3|Storage|Zanzibar + native ACL|Cached (1-5min)|

**Cache Hierarchy**:

* L1: In-process cache (per service instance), TTL 5-60s
* L2: Distributed cache (cross-instance, same region), TTL 1-5min
* L3: Zanzibar server cache (global), TTL 5-30min
* Invalidation: Write to Zanzibar -> broadcast invalidation -> caches refresh

**Critical dependency**: Zanzibar depends on Spanner (tuple storage) and Chubby (leader election). Failure -> all services potentially deny requests (fail-closed) or allow cached results (fail-open with staleness).

Source: Zanzibar: Google's Consistent, Global Authorization System, USENIX ATC 2019

### 8.2 ACL Engine

* Legacy: Direct ACL lists per object
* Modern: Zanzibar replaces most ACL use cases
* Migration: ACLs -> Zanzibar tuples (gradual)

### 8.3 Access-Control Graph

* Nodes: Users, groups, resources, roles
* Edges: Relations (member, owner, viewer)
* Traversal: Graph expansion for authorization decisions
* Cycles: Detected and handled (typically deny)

\---

## LAYER 9: DATA PROCESSING LAYER

### The Digestive System

### 9.1 MapReduce

MapReduce simplifies data processing on large clusters.

**Model**:

* Map: Read input, emit key-value pairs
* Shuffle: Sort by key
* Reduce: Aggregate values per key

**Usage**: Batch indexing, log analysis, data transformation

Source: MapReduce: Simplified Data Processing on Large Clusters, OSDI 2004

### 9.2 FlumeJava

FlumeJava is a Java library for easy, efficient data-parallel pipelines.

**Core abstractions**:

* **PCollection<T>**: Immutable parallel collection
* **PTable<K,V>**: Immutable multi-map
* **parallelDo()**: Element-wise computation
* **groupByKey()**: Group by key
* **combineValues()**: Associative combining
* **flatten()**: Merge collections

**Execution**: Deferred evaluation -> internal execution plan (dataflow graph) -> optimization -> execution on MapReduce primitives.

**Result**: Optimized execution plan typically several times faster than hand-optimized chain of MapReduce jobs.

**Usage**: Hundreds of pipeline developers within Google.

Source: FlumeJava: Easy, Efficient Data-Parallel Pipelines, PLDI 2010

### 9.3 Sawzall

Sawzall is a domain-specific language for logs processing, implemented as a layer over MapReduce.

**Purpose**: Parallel analysis of large log datasets.

Source: Interpreting the Data: Parallel Analysis with Sawzall, Scientific Programming 2005

\---

## LAYER 10: OBSERVABILITY AND RECOVERY

### The Diagnostic System

### 10.1 Dapper — Distributed Tracing

Dapper is Google's large-scale distributed systems tracing infrastructure.

**Design goals**:

1. Low overhead (negligible performance impact)
2. Application-level transparency (no developer awareness needed)
3. Scalability (Google-scale)
4. Quick availability (data available within a minute)

**Data model**:

* **Trace**: Tree of nested RPCs representing a request's journey
* **Span**: Single unit of work, with start/end timestamps, operation name, parent reference
* **Trace ID**: 64-bit probabilistically unique integer shared by all spans in a trace
* **Span ID**: 64-bit integer per span
* **Annotations**: Application-specific metadata (timestamped key-value pairs)

**Instrumentation**:

* Integrated into threading, control flow, and RPC libraries
* Trace context stored in thread-local storage
* Propagated through callbacks and RPCs
* Language-independent: combines C++ and Java traces

**Collection pipeline**:

1. Span data written to local log files
2. Dapper Daemons pull from all production hosts
3. Written to regional Bigtable repositories
4. **Median latency**: <15 seconds from application to central repository

**Sampling**: Deterministic upfront sampling (e.g., 0.01% of requests). Once sampled, all subsequent spans captured.

**Privacy**: Stores RPC method names, not payload data. Application-level annotations are opt-in.

Source: Dapper, a Large-Scale Distributed Systems Tracing Infrastructure, 2010

### 10.2 Monarch — Time Series Database

Monarch is a globally-distributed in-memory time series database.

**Scale**:

* Ingests **terabytes of data per second**
* Stores close to a **petabyte** of compressed time series data in memory
* Serves **millions of queries per second**
* Manages **trillions of time series**

**Architecture**:

* **Regionalized**: Autonomous zones with local monitoring
* **Global planes**: Query and configuration integrate regions into unified system
* **Components by function**:

  * State: Leaves (in-memory store), Recovery Logs (local disk), Global Config Server (Spanner)
  * Ingestion: Ingestion Routers, Leaf Routers, Range Assigners
  * Query: Query Executors

**Data model**:

* Schematized tables with key columns (targets + metrics) and value column (time series history)
* **Targets**: Associate time series with source entity (e.g., ComputeTask with fields: user, job, cluster, task num)
* **Location field**: Determines which Monarch zone stores the time series
* Target ranges: Lexicographic sharding and load balancing among leaves

**Independence requirement**: Bigtable, Colossus, Spanner, and Blobstore use Monarch for monitoring. Therefore, Monarch cannot depend on these systems on the alerting path to avoid circular dependency.

Source: Monarch: Google's Planet-Scale In-Memory Time Series Database, VLDB 2020

### 10.3 Borgmon

Borgmon was Google's initial monitoring system, predecessor to Monarch.

**Limitations that led to Monarch**:

1. Decentralized operational model — each team managed own Borgmon instances
2. No schematization for measuring dimensions and metric values
3. No good support for distribution value type
4. Required manual sharding of monitored entities

Source: Monarch paper, VLDB 2020

### 10.4 Alerting and Incident Management

* **Severity**: P1 (outage) to P5 (minor)
* **Response**: Automated runbooks -> human escalation
* **Post-mortem**: Mandatory within 5 business days
* **SLO-based alerting**: Not threshold-based, but based on error budget burn rate

### 10.5 Failure Recovery

* **Auto-remediation**: Restart, migrate, drain
* **Circuit breakers**: Stop sending traffic to failing instances
* **Chaos engineering**: DiRT (Disaster Recovery Training) exercises — intentional failures to test recovery

\---

## LAYER 11: SAFETY / SECURITY LAYER

### The Fortification

### 11.1 Infrastructure Security Design

* **Zero trust**: No implicit trust based on network location
* **Defense in depth**: Multiple independent controls
* **Least privilege**: Minimal access for every component

### 11.2 Identity and Access Management

* **User identity**: Google Accounts, SSO, 2FA
* **Service identity**: SPIFFE/SPIRE-style service accounts
* **Authentication**: OAuth 2.0, mutual TLS

### 11.3 Secret Management

* Encrypted at rest, access-logged
* Short-lived tokens, automatic rotation
* Per-service, per-environment scope

### 11.4 Attestation

* **Binary provenance**: Who built this, from what source
* **Runtime attestation**: Is this binary unmodified
* **Hardware**: TPM-based attestation where available

### 11.5 Isolation Boundary

* **VM-level**: KVM-based virtualization
* **Container-level**: Namespaces, cgroups, seccomp
* **Process-level**: Sandboxing

### 11.6 gVisor — Sandbox Layer

gVisor is a user-space kernel that intercepts syscalls for deep isolation.

**Components**:

* **Sentry**: Complete independent user-space OS kernel in Go. Intercepts, validates, and services syscalls without passing to host kernel.
* **Gofer**: Separate isolated process for filesystem operations. Communicates with Sentry via 9P protocol.

**Modes**:

* **KVM mode**: Hardware virtualization via /dev/kvm, near-native performance
* **Ptrace mode**: Standard Linux ptrace API, universally compatible

**Use cases**:

* Multi-tenant AI workloads
* Dynamic data ingestion engines
* Zero-trust microservice execution

Source: gVisor documentation; Google Cloud security architecture

### 11.7 Supply-Chain Security

* **Source control**: Piper (monorepo), code review required
* **Build**: Hermetic builds, reproducible where possible
* **Deployment**: Binary verification, gradual rollouts
* **Dependency**: Vulnerability scanning, license compliance

### 11.8 Piper — Monorepo

Google stores billions of lines of code in a single repository (Piper).

**Properties**:

* Single unified version control system
* All code visible to all engineers (with ACLs)
* Atomic changes across multiple projects
* Unified build system (Blaze/Bazel)
* Enables large-scale refactoring and code analysis

Source: Why Google Stores Billions of Lines of Code in a Single Repository, CACM 2016

\---

## INTEGRATED DATA FLOW: HAPPY PATH

```
1. INGRESS (Layer 1)
   User -> DNS -> Anycast IP -> BGP Edge -> GSLB -> Nearest PoP -> GFE
   GFE: TLS termination, HTTP parsing, Zanzibar authN check

2. LOAD BALANCING (Layer 1)
   Maglev/Envoy -> Consistent hash -> Backend service instance
   Health check: Is backend alive?

3. NETWORK TRANSIT (Layer 1)
   Clos fabric -> Jupiter SDN -> Destination rack
   TE: Optimal path selected

4. SERVICE EXECUTION (Layer 2)
   Borglet -> Container -> Application code
   Zanzibar authZ check: Can user access this resource?

5. RPC (Layer 7)
   Stubby/gRPC -> Protocol Buffers serialization
   To other services or storage

6. DATA ACCESS (Layer 6)
   Service -> Spanner/Bigtable/Colossus client
   Zanzibar authZ check: Can user read/write this data?

7. STORAGE (Layer 6)
   Tablet server -> Paxos group -> WAL -> Colossus chunk
   TrueTime: Timestamp assigned
   Replication: 3x confirmed

8. RESPONSE (Reverse path)
   Data -> Service -> Load Balancer -> Edge -> User
   Telemetry: Metrics (Monarch), logs, traces (Dapper) emitted
```

\---

## FAILURE PROPAGATION ANALYSIS

### Infrastructure Failures

|Failure|Impact|Mitigation|Cascade Risk|
|-|-|-|-|
|Single NIC failure|1 server offline|Borg reschedules tasks|Low|
|ToR switch failure|40-80 servers offline|ECMP reroutes, Borg reschedules|Medium|
|Fabric link cut|Reduced bandwidth|TE reroutes traffic|Medium|
|Datacenter partition|Split-brain risk|Paxos quorums, stale reads|High|
|Region failure|Service unavailable|Multi-region replication, GSLB failover|High|
|GPS time source failure|TrueTime uncertainty up|Atomic clock holdover, secondary GPS|Medium|

### Application Failures

|Failure|Impact|Mitigation|Cascade Risk|
|-|-|-|-|
|Zanzibar overload|Auth checks slow/fail|Cache, circuit breaker, degraded mode|Critical|
|Spanner Paxos leader loss|Writes stall (10-30s)|Automatic leader election|High|
|Bigtable tablet hotspot|Latency spike|Split tablet, load rebalance|Medium|
|Chubby session timeout|Leader elections, config stale|Session renewal, caching|Critical|
|Borgmaster partition|Scheduling stops|Running tasks continue, cache|High|

### Cascading Failure: Zanzibar Overload

1. Zanzibar query latency increases (cache miss storm)
2. Services wait for auth checks -> thread pool exhaustion
3. Services return 503 -> Load balancer retries
4. Retries amplify load -> More Zanzibar queries
5. Zanzibar itself becomes overloaded
6. All services deny requests (fail-closed) OR allow cached (fail-open, security risk)

**Circuit breaker intervention**: After N failures/timeout, stop calling Zanzibar. Use cached decision (stale but available). Alert: "Degraded authorization mode".

\---

## PRIMARY SOURCES

|#|Paper / Source|Conference / Venue|Year|
|-|-|-|-|
|1|The Google File System (GFS)|SOSP|2003|
|2|MapReduce: Simplified Data Processing on Large Clusters|OSDI|2004|
|3|Interpreting the Data: Parallel Analysis with Sawzall|Scientific Programming|2005|
|4|The Chubby Lock Service for Loosely-Coupled Distributed Systems|OSDI|2006|
|5|Bigtable: A Distributed Storage System for Structured Data|OSDI|2006|
|6|Dapper, a Large-Scale Distributed Systems Tracing Infrastructure|Google Technical Report|2010|
|7|FlumeJava: Easy, Efficient Data-Parallel Pipelines|PLDI|2010|
|8|Large-scale Cluster Management at Google with Borg|EuroSys|2015|
|9|Jupiter Rising: A Decade of Clos Topologies and Centralized Control|SIGCOMM|2015|
|10|B4: Experience with a Globally-Deployed Software Defined WAN|SIGCOMM|2013|
|11|Maglev: A Fast and Reliable Software Network Load Balancer|NSDI|2016|
|12|Spanner: Google's Globally-Distributed Database|OSDI|2012|
|13|F1: A Distributed SQL Database That Scales|VLDB|2012|
|14|Zanzibar: Google's Consistent, Global Authorization System|USENIX ATC|2019|
|15|Monarch: Google's Planet-Scale In-Memory Time Series Database|VLDB|2020|
|16|Andromeda: Performance, Isolation, and Velocity at Scale|NSDI|2018|
|17|BwE: Flexible, Hierarchical Bandwidth Allocation|SIGCOMM|2015|
|18|Jupiter Evolving: Transforming Google's Datacenter Network|SIGCOMM|2022|
|19|Why Google Stores Billions of Lines of Code in a Single Repository|CACM|2016|
|20|Site Reliability Engineering (SRE Book)|O'Reilly|2016|
|21|Lessons Learned from B4, Google's SDN WAN|USENIX ATC|2015|

\---

## COMPONENT QUICK REFERENCE

|Component|Layer|Function|Depends On|Critical Failure|
|-|-|-|-|-|
|Colossus|0/6|Distributed storage|Chubby, Network|Master partition|
|Jupiter|1|Datacenter network|Physical, Chubby|Controller failure|
|B4|1|Inter-DC WAN|Physical, SDN|TE algorithm failure|
|Andromeda|1|Cloud virtualization|Jupiter, Physical|Control plane overload|
|Maglev|1|Load balancing|Health checks|Consistent hash disruption|
|GSLB|1|Global traffic|DNS, Health|Misconfiguration|
|GFE|1|Front end proxy|GSLB, TLS certs|DDoS overload|
|Borg|2|Cluster management|Chubby|Scheduling halt|
|Chubby|3|Coordination|Paxos, Network|Session timeout cascade|
|TrueTime|4|Global timestamps|GPS, Atomic clocks|Uncertainty increase|
|Spanner|6|Global database|TrueTime, Chubby, Colossus|Paxos leader loss|
|Bigtable|6|NoSQL store|Chubby, Colossus|Tablet hotspot|
|F1|6|SQL on Spanner|Spanner|Inherited from Spanner|
|Stubby|7|Internal RPC|Network|Service discovery failure|
|Protobuf|7|Serialization|N/A (format)|Schema incompatibility|
|Zanzibar|8|Authorization|Spanner, Chubby|Auth storm|
|Dapper|10|Distributed tracing|Bigtable|Data loss (non-critical)|
|Monarch|10|Monitoring|Independent|Data loss (non-critical)|
|Borgmon|10|Legacy monitoring|Borg|Replaced by Monarch|
|gVisor|11|Sandbox|Host kernel|Escape vulnerability|
|Piper|11|Monorepo|Storage|VCS unavailability|

\---



