[README.md](https://github.com/user-attachments/files/26923449/README.md)
# 13.10.1307
MENE, MENE, TEKEL, UPHARSIN


This report synthesizes academic and technical research spanning 2020–2026 across three interconnected domains: (1) DoD cloud security architecture including the Secure Cloud Computing Architecture (SCCA), Common Access Card (CAC)/Public Key Infrastructure (PKI) standards, CNSSI 1253 controls, and Impact Level 6 (IL6) authorization; (2) Extended Berkeley Packet Filter (eBPF) kernel-level security verification, Cilium networking, and Kubernetes runtime security; and (3) the emerging intersection of these domains through bpfd (now bpfman) Kubernetes operators, node credential verification eBPF programs, and Zero Trust Architecture (ZTA) implementations in classified cloud environments.

---

## 2. DoD CAC/PKI Standards & Trusted Cloud Credential Manager (TCCM)

### 2.1 Foundational Policy Framework: DoD Instruction 8520.02

**DoD Instruction 8520.02** ("Public Key Infrastructure and Public Key Enabling") establishes the comprehensive framework for DoD PKI implementation. The May 2023 update mandates:

- DoD-wide PKI maintaining full certificate lifecycle (issuance, suspension, revocation)
- First- and third-party key recovery for encryption certificate private keys
- PKI enabling for digital signature and encryption across all DoD information systems
- Mandatory use of DoD PKI or DoD-approved PKI certificates for authentication, digital signature, and encryption
- Cross-certification with the Federal PKI for FIPS 201-1 compliance
- Mandatory CAC certificates for all person-entity authentication

The instruction requires all CSPs to implement PKI-based authentication at IL5 and IL6, with non-PKI MFA alternatives permitted only under specific AAL2/AAL3 requirements per NIST SP 800-63A.

### 2.2 Trusted Cloud Credential Manager (TCCM)

The TCCM is designated as an individual or entity appointed by the DoD mission owner's Authorizing Official (AO) to establish plans and policies for controlling privileged user access. Research from the DoD SCCA Functional Requirements Document identifies the TCCM as responsible for:

- Developing and maintaining a Cloud Credential Management Plan (CCMP)
- Collecting, auditing, and archiving all Customer Portal activity logs and alerts
- Creating, issuing, and revoking role-based, least-privileged customer portal credentials
- Ensuring privileged users cannot unilaterally create unauthorized network connections
- Recovering and securely controlling customer portal account credentials prior to DISN connectivity

### 2.3 Academic Papers on PKI/Cloud Authentication

| # | Title | Authors | Year | Citations |
|---|-------|---------|------|-----------|
| 1 | Enhancing Identity and Access Management in the US Navy Via Migration to More Modern Standards of Authentication | RS Baxter, CS Martinez Jr | 2020 | 1 |
| 2 | Powerful authentication regime applicable to naval OFP integrated development (PARANOID) | J Garcia, R Shannon, A Jacobson, W Mosca et al. | 2021 | 3 |
| 3 | Platform attestation in consumer devices | A Niemi, V Nayani, M Moustafa et al. | 2023 | 5 |
| 4 | Software trusted startup and update protection scheme of IoT devices | M Zhang, Y Zhang, S Li, Q Wan | 2023 | 2 |
| 5 | Verifiable Quantum ABE: Binding Policy Evaluation to Post-Quantum Cryptography | G Mogos | 2025 | 0 |
| 6 | Tackling data mining risks: A tripartite covert channel merging blockchain and IPFS | Z Chen, L Zhu, P Jiang, J He et al. | 2025 | 20 |

---

## 3. Virtual Datacenter Security Stack (VDSS), VDMS & Boundary Cloud Access Point (BCAP)

### 3.1 SCCA Framework Architecture

The **Secure Cloud Computing Architecture (SCCA)**, established by DISA in 2018 and refined through 2024, provides the foundational security framework for DoD cloud deployments at IL4 and IL5 (with extensions to IL6). The four primary technical components are:

**Cloud Access Point (CAP):**
- **Boundary CAP (BCAP):** Connects DISN/NIPRNet to commercial cloud; protects DISN from cloud-originating attacks
- **Internet CAP (ICAP):** Provides internet-facing connectivity
- **Component CAP (CCAP):** Component-level access control
- Functions: Cloud connectivity, DISN protection, traffic inspection

**Virtual Datacenter Security Stack (VDSS):**
- Web Application Firewall (WAF)
- Next-Generation Firewall (NGFW) with intrusion prevention/detection
- Network routing and firewall rules
- Serves as the virtual security enclave protecting applications and data

**Virtual Datacenter Managed Service (VDMS):**
- Intrusion Prevention/Detection Systems (IPS/IDS)
- Identity management services (CAC/PKI authentication integration)
- Domain services, OCSP services, directory services
- Security and access policy enforcement
- Application access rules, bastion hosts, DMZ services

**Trusted Cloud Credential Manager (TCCM):**
- Least-privilege ABAC account management
- Root credential control and role-based access rights issuance
- CCMP development and maintenance

### 3.2 Impact Level 6 (IL6) Authorization & CNSSI 1253

**CNSSI 1253** ("Security Categorization and Control Selection for National Security Systems") provides the control selection framework for all DoD NSS cloud environments. Key research findings include:

- **Space Segment Cybersecurity Profile for National Security Systems-Revision A** (Roeher et al., 2024): Documents how CNSSI 1253 baselines require tailoring for space-based NSS, with IL6 representing classified information up to Secret level requiring FedRAMP High baseline plus CNSSI 1253 overlays for High Confidentiality and Integrity.

- The DoD CSP SRG v1r2 (2016) and subsequent updates mandate that IL6 CSOs must:
  - Leverage FedRAMP High baseline
  - Include CNSSI 1253 overlays in Appendix D for High Confidentiality and Integrity
  - Implement additional NSS controls for National Security Systems
  - Maintain physical/data separation requirements per DoD Jurisdiction Location requirements

### 3.3 JWCC & Compute as a Service for Secret Cloud

The **Joint Warfighting Cloud Capability (JWCC)** contract vehicle (replacing JEDI) provides multi-cloud infrastructure services across all impact levels. Research by Vidal & Colclough (2024) documents how JWCC integrates with SCCA architecture, enabling:

- DISA-approved Cloud Service Offerings at IL2, IL4, IL5, and IL6
- Standardized boundary protection through SCCA components
- Compute as a Service for Secret Cloud environments

---

## 4. eBPF Runtime Security & Kernel Verification

### 4.1 The eBPF Verifier: Formal Verification Research

The eBPF verifier is the Linux kernel's primary defense mechanism for ensuring eBPF program safety. Significant academic research has focused on formal verification:

**Key Papers:**

| # | Title | Venue | Year | Citations |
|---|-------|-------|------|-----------|
| 1 | **Validating the eBPF Verifier via State Embedding** | USENIX OSDI | 2024 | High |
| 2 | **SoK: Challenges and Paths Toward Memory Safety for eBPF** | IEEE S&P | 2025 | New |
| 3 | **VEP: A Two-stage Verification Toolchain for Full eBPF Programmability** | USENIX NSDI | 2025 | New |
| 4 | **Simple and Precise Static Analysis of Distributed Linux Kernel Extensions** | PLDI | 2019 | High |
| 5 | **Kernel Extension Verification Is Untenable** | ACM SIGOPS HotOS | 2023 | High |
| 6 | **MOAT: Towards Safe BPF Kernel Extension** | USENIX Security | 2024 | High |
| 7 | **HIVE: Hardware-Assisted Isolated Execution Environment for eBPF on AArch64** | USENIX Security | 2024 | High |
| 8 | **eBPF: Pioneering kernel programmability and system observability** | IEEE ICAINI | 2024 | 8 |
| 9 | **The eBPF Runtime in the Linux Kernel** | arXiv | 2024 | 21 |
| 10 | **Unleashing Unprivileged eBPF with Dynamic Sandboxing** | SIGCOMM eBPF Workshop | 2023 | 10+ |

The **state embedding** technique (Sun & Su, OSDI 2024) uncovered 15 previously unknown logic bugs in the eBPF verifier within one month, 10 of which were exploitable for local privilege escalation. This research validated the verifier's correctness through embedding concrete states as correctness checks within eBPF programs.

### 4.2 eBPF Container Security & Cross-Container Attacks

The landmark paper **"Cross Container Attacks: The Bewildered eBPF on Clouds"** (He et al., USENIX Security 2023, 68 citations) demonstrated how offensive eBPF capabilities can break container isolation and attack hosts. The research:

- Successfully compromised five online Jupyter/Interactive Shell services and Google Cloud Platform's Cloud Shell
- Demonstrated cross-node attacks after container escape via eBPF on Kubernetes services from three major cloud vendors
- Showed that Alibaba's Kubernetes services could have entire clusters compromised via over-privileged cloud metrics/management Pods
- Proposed a new eBPF permission model for secure container usage

### 4.3 Cilium: eBPF-Based Kubernetes Networking & Security

Cilium has emerged as the de facto eBPF-based Container Network Interface (CNI) for Kubernetes security:

**Key Research:**

| # | Title | Authors | Year | Citations |
|---|-------|---------|------|-----------|
| 1 | **Delineating Cilium Core Architecture** | DM Ghane | 2025 | 1 |
| 2 | **Secure inter-container communications using XDP/eBPF** | J Nam, S Lee, P Porras et al. | 2022 | 31 |
| 3 | **An abstract model of cloud-native networks for security enforcement** | G Lisena | 2025 | 0 |
| 4 | **Elevating Kubernetes network security through Cilium** | (FH Joanneum thesis) | 2025 | NA |
| 5 | **Preventing IP Spoofing in Kubernetes Using eBPF** | A Hussain, A Aziz, S Hassan et al. | 2025 | 0 |

The Cilium Security Audit 2022 identified key areas including type confusion risks in Go-based eBPF management, the eBPF datapath architecture (XDP, TC, socket hooks), and supply chain security considerations for eBPF-based infrastructure.

---

## 5. bpfd (bpfman) Kubernetes Operator & eBPF Program Management

### 5.1 bpfd.dev/v1alpha1 CRD Architecture

The **bpfd** project (now **bpfman**) provides a Kubernetes-native eBPF management system using Custom Resource Definitions (CRDs). The architecture includes:

**CRD Types:**
- `XdpProgram` (bpfd.dev/v1alpha1)
- `TcProgram` (bpfd.dev/v1alpha1)
- `TracepointProgram` (bpfd.dev/v1alpha1)
- `KprobeProgram` (bpfd.dev/v1alpha1)
- `UprobeProgram` (bpfd.dev/v1alpha1)
- `BpfProgram` (per-node status reporting)

**Reconciliation Status:**
The operator uses `ReconcileSuccess` type conditions to report eBPF program deployment status:

```yaml
status:
  conditions:
  - lastTransitionTime: "2023-05-04T15:41:45Z"
    message: bpfProgramReconciliation Succeeded on all nodes
    reason: ReconcileSuccess
    status: "True"
    type: ReconcileSuccess
```

This status indicates successful reconciliation of eBPF bytecode across all selected cluster nodes.

### 5.2 Bytecode Image Distribution

bpfd supports packaging eBPF programs as OCI container images for secure distribution:

```yaml
bytecode:
  image:
    url: quay.io/bpfd-bytecode/go-xdp-counter:latest
```

This approach enables supply chain security through container image signing, RBAC-controlled deployment, and versioning independent of userspace components.

### 5.3 Key Benefits

- **Security:** Only bpfd daemon requires BPF privileges; API access controlled via RBAC
- **Visibility:** Reports all eBPF programs running across cluster nodes
- **Multi-program support:** Multiple XDP/TC programs per interface with priority ordering
- **Productivity:** Simplifies lifecycle management of eBPF programs at scale

---

## 6. eBPF Go Development: bpf2go & Cilium/ebpf Library

### 6.1 The cilium/ebpf Go Library

The `cilium/ebpf` library is the predominant Go-based toolkit for eBPF program development. Research from Linux Plumbers Conference 2021 documented the library's approach to:

- ELF loader integration for eBPF program loading
- Go type generation via `go:generate` directives
- Map and program management abstractions
- Integration with kernel BPF subsystem features

### 6.2 bpf2go Code Generation

The `bpf2go` tool compiles C eBPF programs and generates Go bindings:

**Typical workflow:**
```go
//go:generate go run github.com/cilium/ebpf/cmd/bpf2go -target bpfel bpf program.c

// Generated structures include:
// type bpfSpecs struct { ... }
// type bpfObjects struct { ... }
// func loadBpfObjects(obj interface{}, opts *ebpf.CollectionOptions) error
```

The tool handles:
- C to eBPF bytecode compilation (via clang)
- Go struct generation for map and program access
- Little-endian/big-endian target support
- BTF (BPF Type Format) information preservation

### 6.3 verify_node_credentials Pattern

The `verify_node_credentials` pattern represents a class of eBPF programs for node-level identity verification in Kubernetes clusters. Such programs typically:

- Attach to XDP, TC, or cgroup/sock hooks
- Validate pod/container identity through kernel-level metadata
- Check credentials against eBPF maps populated by Kubernetes controllers
- Use `pid` (int32) fields in bpf2go-generated structs for process identification

---

## 7. eBPF Hook Types: XDP, TC, Tracepoint, Kprobe, Uprobe

### 7.1 Program Type Characteristics

| Hook Type | Attachment Point | Use Case | Execution Context |
|-----------|-----------------|-|-------------------|
| **XDP** | Network driver (earliest) | DDoS mitigation, load balancing, packet filtering | Driver RX path |
| **TC (Traffic Control)** | Traffic control layer | Network policy enforcement, QoS, shaping | Network stack |
| **Tracepoint** | Predefined kernel markers | System call tracing, kernel event monitoring | Kernel tracepoint |
| **Kprobe** | Kernel function entry/return | Dynamic kernel instrumentation, debugging | Kernel function |
| **Uprobe** | Userspace function entry/return | Application-level tracing, library monitoring | Userspace function |
| **Cgroup/Sock** | Socket operations | Container network policy, service mesh | Socket layer |

### 7.2 Research on Hook Type Security

**"Analysis and Testing of eBPF Attack Surfaces"** (Messina, 2024) and **"Detection and Mitigation of eBPF Security Risks in the Linux Kernel"** (Costanzo, 2025) provide comprehensive analysis of security implications across hook types. Key findings:

- XDP programs execute at highest privilege with lowest latency
- TC programs have access to sk_buff for rich packet inspection
- Tracing programs (tracepoint, kprobe, uprobe) can access kernel internal state
- Verifier limitations vary by program type, creating differential attack surfaces

---

## 8. Kubernetes Security: CVEs, Operators & Reconciliation

### 8.1 CVE Analysis in Kubernetes Environments

**"A Container Security Survey: Exploits, Attacks, and Defenses"** (Jarkas et al., ACM Computing Surveys 2025, 43 citations) analyzes 200+ vulnerabilities including:

- CVE-2020-8557: Kubernetes resource exhaustion
- CVE-2019-16276: API server authentication bypass
- CVE-2024-23653: Container build vulnerabilities
- CVE-2024-21626: BuildKit container escape

### 8.2 Kubernetes Operator Patterns

The **Koney** framework (Kahlhofer et al., arXiv 2025) demonstrates cyber deception orchestration for Kubernetes using:
- Custom Resource Definitions for deception policy
- eBPF and service mesh for trap deployment
- Automated rotation, monitoring, and removal
- Source-code-independent protection

### 8.3 ReconcileSuccess Status Pattern

The `ReconcileSuccess` condition type is used by Kubernetes operators (including bpfd/bpfman) to indicate successful reconciliation of desired state. This pattern:
- Provides declarative status reporting for eBPF program deployment
- Enables GitOps workflows for kernel-level program management
- Supports progressive rollout monitoring across cluster nodes

---

## 9. F5 BIG-IP & Cloud-Native Load Balancing

### 9.1 F5 BIG-IP Integration Patterns

F5 BIG-IP serves as a key component in VDSS implementations for:
- Advanced application delivery control
- JSON-based API request inspection (`JSON_REQUEST` events)
- SSL/TLS termination with DoD PKI certificate integration
- Web Application Firewall (WAF) functionality

### 9.2 Cloud-Native Alternatives

Research documents the migration from hardware load balancers to eBPF-based solutions:
- Cilium's XDP-based edge load balancing with Maglev consistent hashing
- Direct Server Return (DSR) with session affinity
- kube-proxy replacement at the `connect()` system call level

---

## 10. NAICS 518210 & DoD Cloud Contracting

### 10.1 Industry Classification

**NAICS 518210** ("Data Processing, Hosting, and Related Services") is the primary classification code for:
- Cloud computing services (IaaS, PaaS, SaaS)
- Managed security services
- Data processing and hosting

Research from the Naval Postgraduate School (2021) confirms DoD uses NAICS 518210 for cloud computing requirements per the DoD Taxonomy for Acquisition of Services and Supplies & Equipment.

### 10.2 Related Federal IT NAICS Codes

| NAICS Code | Description | Federal Application |
|------------|-------------|---------------------|
| 518210 | Data Processing, Hosting, and Related Services | Cloud infrastructure, FedRAMP hosting |
| 541519 | Other Computer Related Services | Cybersecurity, IT infrastructure |
| 541512 | Computer Systems Design Services | System integration, cloud migration |
| 541511 | Custom Computer Programming Services | Custom development, AI/ML applications |
| 511210 | Software Publishers | Commercial software licensing |

### 10.3 W519TC25FA214 Task Order

The **W519TC25FA214** task order represents the "Compute as a Service for Secret Cloud" requirement, supporting:
- IL6 Secret Cloud environments
- Managed Kubernetes services
- Cross-domain data movement
- Compute, storage, and database services at classified levels

---

## 11. Zero Trust Architecture & DoD Cloud Security

### 11.1 ZTA Implementation Research

**"Zero Trust (ZT) Concepts for Federal Government Architectures"** (Uttecht, 2020, 46 citations) established foundational concepts adopted across DoD cloud implementations.

**"Security of Zero Trust Networks in Cloud Computing: A Comparative Review"** (Sarkar et al., Sustainability 2022, 211 citations) provides comprehensive analysis of ZTA frameworks from NIST, CISA, DoD, and OMB.

**"Zero Trust Cloud Security Architectures with AI-Orchestrated Policy Enforcement"** (Ibitoye, 2023, 35 citations) proposes AI-enhanced ZTA specifically for critical US sectors including military readiness.

### 11.2 DoD ZTA Reference Architecture

The DoD Zero Trust Reference Architecture (2021-2024) mandates:
- Continuous authentication and authorization
- Micro-segmentation of network resources
- Assume breach mentality
- Least privilege access enforcement
- Comprehensive monitoring and analytics

---

## 12. High-Order Hierarchical Ontology

### 12.1 Ontological Structure

The research domains can be organized hierarchically:

```
DoD Cloud Security Architecture (Root)
├── Identity & Access Management
│   ├── DoD CAC/PKI (DoDI 8520.02)
│   ├── TCCM/CCMP
│   └── Non-PKI MFA (AAL2/AAL3)
├── Boundary Protection
│   ├── SCCA Framework
│   │   ├── BCAP/CAP
│   │   ├── VDSS
│   │   ├── VDMS
│   │   └── TCCM
│   └── CNSSI 1253 Controls
├── Impact Levels
│   ├── IL2 (Non-Controlled Unclassified)
│   ├── IL4 (Controlled Unclassified/CUI)
│   ├── IL5 (CUI + NSS)
│   └── IL6 (Classified/Secret)
├── eBPF Runtime Security
│   ├── Kernel Verification
│   │   ├── eBPF Verifier
│   │   ├── Formal Methods
│   │   └── State Embedding
│   ├── Program Types
│   │   ├── XDP
│   │   ├── TC
│   │   ├── Tracepoint
│   │   ├── Kprobe/Uprobe
│   │   └── Cgroup/Sock
│   ├── Kubernetes Integration
│   │   ├── bpfd/bpfman Operator
│   │   ├── Cilium CNI
│   │   └── Tetragon Runtime
│   └── Security Monitoring
│       ├── Container Escape Detection
│       ├── IP Spoofing Prevention
│       └── Credential Verification
└── Contract & Compliance
    ├── NAICS 518210
    ├── JWCC/GDC
    └── FedRAMP+ DoD SRG
```

---

## 13. Synthesis: The Convergence of eBPF and DoD Cloud Security

### 13.1 Emerging Research Directions

The convergence of eBPF technology with DoD cloud security requirements represents a rapidly evolving research frontier. Key intersection points include:

**eBPF for IL6 Node Credential Verification:**
- Real-time verification of CAC/PKI credentials at the kernel level
- Integration with VDMS identity management services
- Low-overhead enforcement of access control policies

**eBPF-based BCAP Traffic Inspection:**
- XDP-accelerated packet inspection at boundary access points
- TC-based deep packet inspection for classified traffic
- Integration with F5 BIG-IP JSON_REQUEST processing

**Kubernetes Operator Patterns for SCCA Compliance:**
- bpfd-based deployment of security eBPF programs across IL6 clusters
- ReconcileSuccess-based compliance status reporting
- Automated remediation via eBPF-enforced policies

### 13.2 Key Research Gaps

1. **Formal verification of eBPF programs handling classified data**
2. **eBPF verifier correctness proofs for security-critical program types**
3. **Side-channel attack mitigation in multi-tenant eBPF environments**
4. **Cross-domain eBPF program validation for IL6 boundaries**
5. **eBPF-based continuous compliance monitoring for CNSSI 1253 controls**

---

## 14. Complete Bibliography

### 14.1 DoD PKI, Cloud Security & SCCA Framework

1. Roeher BV, De Naray PJ, Bailey BT, Faigin DP. "Space Segment Cybersecurity Profile for National Security Systems-Revision A." DTIC, 2024.
2. Vidal R, Colclough C. "A DoD Initiative to Accelerate Test and Evaluation through Edge and Cloud Computing." Naval Engineers Journal, 2024.
3. DISA. "DoD Secure Cloud Computing Architecture Functional Requirements." DISA, 2017-2024.
4. DoD CIO. "Cloud Security Playbook Volume 1." DoD CIO, 2025.
5. Schellman. "DoD CSP SRG & DoD MO SRG Explained." 2024.
6. Gonzales D, Harting S, Adgie MK, Brackup J, Polley L. "Unclassified and secure: a defense industrial base cyber protection program." DTIC, 2020 (16 citations).
7. Hatuka T, Carmel E. "The Dynamics of the Largest Cybersecurity Industrial Clusters." Tel Aviv University, 2021.
8. Hooton C. "An Industry-Based Estimation Approach for Measuring the Cloud Economy." SSRN, 2020.

### 14.2 eBPF Kernel Security & Verification

9. Sun H, Su Z. "Validating the eBPF Verifier via State Embedding." USENIX OSDI, 2024.
10. Nelson L, Van Geffen J, Torlak E, Wang X. "Specification and verification in the field: Applying formal methods to BPF JIT compilers in the Linux kernel." USENIX OSDI, 2020.
11. Gershuni E, Amit N, Gurfinkel A, Narodytska N, Navas JA, Rinetzky N, Ryzhyk L, Sagiv M. "Simple and precise static analysis of untrusted Linux kernel extensions." PLDI, 2019.
12. Bhat S, Shacham H. "Formal verification of the Linux kernel eBPF verifier range analysis." 2022.
13. Vishwanathan H, Shacham M, Narayana S, Nagarakatte S. "Verifying the Verifier: eBPF Range Analysis Verification." CAV, 2023.
14. Wu X, Feng Y, Huang T, Lu X, Lin S, Xie L, Zhao S, Cao Q. "VEP: A Two-stage Verification Toolchain for Full eBPF Programmability." USENIX NSDI, 2025.
15. "SoK: Challenges and Paths Toward Memory Safety for eBPF." IEEE S&P, 2025.
16. Lu H, Wang S, Wu Y, He W, Zhang F. "MOAT: Towards Safe BPF Kernel Extension." USENIX Security, 2024.
17. Zhang P, Wu C, Meng X, Zhang Y, Peng M, Zhang S, Hu B, Xie M, Lai Y, Kang Y, Wang Z. "HIVE: Hardware-Assisted Isolated Execution Environment for eBPF on AArch64." USENIX Security, 2024.
18. Jia J, Le MV, Oswald A, Williams D, Xu T. "Kernel extension verification is untenable." ACM SIGOPS HotOS, 2023.
19. Gbadamosi B, Leonardi L, Pulls T, et al. "The eBPF Runtime in the Linux Kernel." arXiv:2410.00026, 2024 (21 citations).
20. Song L, Li J. "eBPF: Pioneering kernel programmability and system observability." IEEE ICAINI, 2024 (8 citations).
21. Lim SY, Han X, Pasquier T. "Unleashing Unprivileged eBPF Potential with Dynamic Sandboxing." SIGCOMM eBPF Workshop, 2023.
22. Lim SY, Prasad T, Han X, Pasquier T. "SafeBPF: Hardware-assisted Defense-in-depth for eBPF Kernel Extensions." CCSW, 2024.

### 14.3 eBPF Container & Kubernetes Security

23. He Y, Guo R, Xing Y, Che X, Sun K, Liu Z, et al. "Cross Container Attacks: The Bewildered eBPF on Clouds." USENIX Security, 2023 (68 citations).
24. Nam J, Lee S, Porras P, et al. "Secure inter-container communications using XDP/eBPF." IEEE/ACM Transactions on Networking, 2022 (31 citations).
25. Gwak S, Doan TP, Jung S. "Container Instrumentation and Enforcement System for Runtime Security of Kubernetes Platform with eBPF." IAS, 2023 (16 citations).
26. Fournier G. "Process level network security monitoring and enforcement with eBPF." SSTIC, 2020 (9 citations).
27. Fournier G, Afchain S, Baubeau S. "Runtime security monitoring with eBPF." SSTIC, 2021 (26 citations).
28. Liu C, Cai Z, Wang B, Tang Z, et al. "A protocol-independent container network observability analysis system based on eBPF." IEEE ICPADS, 2020 (80 citations).
29. Cassagnes C, Trestioreanu L, Joly C, et al. "The rise of eBPF for non-intrusive performance monitoring." IEEE/IFIP NOMS, 2020 (69 citations).
30. Lin X, Chen Z, Yang W, Yang X, Luo J. "eBPF-Guard: Container escape detection via multi-level monitoring." Empirical Software Engineering, 2026.
31. Ryu J, Kim R, Lee S, Kim S, Choi H. "Hybrid Runtime Detection of Malicious Containers Using eBPF." 2026.
32. Kim R, Ryu J, Kim S, Lee S, Kim S. "Detecting cryptojacking containers using eBPF-based security runtime and machine learning." Electronics, 2025 (13 citations).
33. Remya S, Pillai MJ, Niranjan B, Kumar PMA. "eBPF based Runtime Detection of Semantic DDoS Attacks in Linux Containers." IEEE, 2025 (2 citations).
34. Zehra S, Syed HJ, Samad F, Faseeha U. "Desfam: An adaptive eBPF and AI-driven framework for securing cloud containers in real time." IEEE Access, 2025 (4 citations).
35. Zhang T, Liu X, Fan B, Huang Y. "Container Path Mis-Resolution Escape Detection Method Based on eBPF." IEEE, 2025.

### 14.4 Cilium & Kubernetes Networking

36. Ghane DM. "Delineating Cilium Core Architecture." Springer, 2025 (1 citation).
37. Budigiri G. "Secure and scalable policy management in cloud native networking." ACM Middleware, 2023 (5 citations).
38. Karakaş B. "Enhancing Security in Communication Applications Deployed on Kubernetes." Aalto University, 2023 (3 citations).
39. Kahlhofer M, Golinelli M, Rass S. "Koney: A Cyber Deception Orchestration Framework for Kubernetes." arXiv:2504.02431, 2025.
40. Lisena G. "An abstract model of cloud-native networks for security enforcement and remediation." Politecnico di Torino, 2025.
41. Tornesello R. "Orchestrating Network Security Borders in the Computing Continuum with Liqo." Politecnico di Torino, 2026.

### 14.5 Kubernetes Security & Vulnerabilities

42. Jarkas O, Ko R, Dong N, Mahmud R. "A container security survey: Exploits, attacks, and defenses." ACM Computing Surveys, 2025 (43 citations).
43. Rahman A, Shamim SI, Bose DB, et al. "Security misconfigurations in open source Kubernetes manifests: An empirical study." ACM TOPS, 2023 (142 citations).
44. Shamim MSI, Bhuiyan FA, et al. "Xi commandments of Kubernetes security." IEEE Secure Development, 2020 (153 citations).
45. Stanišić S, Vesković M, Ristić O, et al. "Security aspects of container orchestration in Kubernetes environments." IEEE, 2025 (4 citations).
46. Mahavaishnavi V, Saminathan R. "Secure container Orchestration: Detecting Orchestrator-level vulnerabilities." Springer, 2025 (16 citations).
47. Huang K, Jumde P. "Learn Kubernetes Security." Packt Publishing, 2020 (26 citations).

### 14.6 Zero Trust & Federal Cloud Security

48. Uttecht KD. "Zero Trust (ZT) Concepts for Federal Government Architectures." DTIC, 2020 (46 citations).
49. Sarkar S, Choudhary G, Shandilya SK, Hussain A. "Security of zero trust networks in cloud computing: A comparative review." MDPI Sustainability, 2022 (211 citations).
50. Ibitoye J. "Zero-Trust cloud security architectures with AI-orchestrated policy enforcement." IJSEA, 2023 (35 citations).
51. Ofili BT, Erhabor EO, Obasuyi OT. "Enhancing federal cloud security with AI: zero trust, threat intelligence, and CISA compliance." WJARR, 2025 (30 citations).
52. Olorunlana TJ. "Autonomous Cloud Security Orchestration for Critical Infrastructure Resilience." IJSA, 2024 (6 citations).
53. Kolawole I. "Advancing US National security with cloud computing." IJETRM, 2025 (3 citations).
54. Kolawole I. "Leveraging Cloud-based AI and zero trust architecture to enhance US cybersecurity." WJARR, 2025 (10 citations).
55. Sahu K, Kumar R, Srivastava RK, Singh AK. "Military computing security: Insights and implications." Springer, 2025 (14 citations).
56. Abd Al Ghaffar HAN. "Government cloud computing and national security." Emerald REPS, 2024 (33 citations).
57. Oshiro DM. "Zero Trust Architecture Implementation for the Marine Corps Tactical Cloud." DTIC, 2023.

### 14.7 eBPF Networking & Performance

58. Abranches M, Michel O, Keller E, et al. "Efficient network monitoring applications in the kernel with eBPF and XDP." IEEE NetSoft, 2021 (75 citations).
59. Zhong Y, Li H, Wu YJ, Zarkadas I, Tao J, et al. "XRP: In-Kernel storage functions with eBPF." USENIX OSDI, 2022 (173 citations).
60. Soldani D, Nahi P, Bour H, Jafarizadeh S, et al. "eBPF: A new approach to cloud-native observability, networking and security for 5G and 6G." IEEE Access, 2023 (89 citations).
61. Her J, Kim J, Kim J, Lee S. "An in-depth analysis of eBPF-based system security tools in cloud-native environments." IEEE Access, 2025 (5 citations).
62. du Perron KC. "Accelerating container networking with eBPF." HAL, 2025.
63. Sharma B. "Improving microservices observability in cloud-native infrastructure using eBPF." 2023.
64. Budigiri G. "Secure and scalable policy management in cloud native networking." ACM Middleware, 2023.

### 14.8 eBPF Analysis & Attack Surfaces

65. Messina A. "Analysis and Testing of eBPF Attack Surfaces." Politecnico di Torino, 2024 (2 citations).
66. Costanzo V. "Detection and Mitigation of eBPF Security Risks in the Linux Kernel." Politecnico di Torino, 2025 (1 citation).
67. Adepoju SA, Adepoju MAO. "Three Modes of Database-Kernel Integration via eBPF." 2026.
68. Jonaitis M. "The research of high-level tracing for Linux extended Berkeley packet filter." 2026.
69. Hedam N. "EBPF-from a programmer's perspective." EasyChair, 2021 (8 citations).

### 14.9 ArXiv Papers

70. Kahlhofer M, Golinelli M, Rass S. "Koney: A Cyber Deception Orchestration Framework for Kubernetes." arXiv:2504.02431, 2025.
71. Knob LAD, Franzil M, Siracusa D. "Exploiting Kubernetes' Image Pull Implementation to Deny Node Availability." arXiv:2401.10582, 2024.
72. Gbadamosi B, Leonardi L, Pulls T, et al. "The eBPF Runtime in the Linux Kernel." arXiv:2410.00026, 2024.

### 14.10 Web Sources & Technical Documentation

73. bpfd project. "bpfd: A Novel Way to Manage eBPF." bpfman.io, 2023.
74. Red Hat. "Using eBPF in unprivileged Pods." 2023.
75. Oracle. "DoD Secure Cloud Computing Architecture (SCCA)." oracle.com, 2023.
76. eunomia.dev. "eBPF Ecosystem Progress in 2024-2025: A Technical Deep Dive." 2025.
77. Oracle. "Oracle Introduces First Cloud Native SCCA Solution for the U.S. DoD." PRNewswire, 2023.
78. AWS. "Secure Cloud Computing Architecture (SCCA) on AWS GovCloud." AWS Architecture Center.
79. AEM Corporation. "Solving the Shared Security Model with SCCA." aemcorp.com.
80. DISA. "DoD Cloud Computing Security Requirements Guide v1r2." DISA, 2016.
81. DoD CIO. "MFA Policy Memorandum for DoD Networks." 2025.

---

*Report compiled from 81+ peer-reviewed papers, government reports, and technical documents published between April 2020 and April 2026.*
