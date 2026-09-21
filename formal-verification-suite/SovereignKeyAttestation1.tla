----------------------- MODULE SovereignKeyAttestation -----------------------
EXTENDS Naturals, Sequences, FiniteSets

CONSTANTS 
    Nodes,
    GoldenPCR,
    ClientVetoReasons

VARIABLES 
    network,
    nodeState,
    kmsKeyPossession,
    clientVetoEnforced

TypeOK ==
    /\ nodeState \in [Nodes -> {"BOOTING", "ATTESTED", "COMPROMISED"}]
    /\ kmsKeyPossession \in BOOLEAN
    /\ clientVetoEnforced \in BOOLEAN

Init ==
    /\ network = {}
    /\ nodeState = [n \in Nodes |-> "BOOTING"]
    /\ kmsKeyPossession = FALSE
    /\ clientVetoEnforced = FALSE

NodeSendTPMQuote(n, currentPCR, nonce) ==
    /\ nodeState[n] = "BOOTING"
    /\ network' = network \cup {[type |-> "TPM_QUOTE", node |-> n, pcr |-> currentPCR, nonce |-> nonce]}
    /\ UNCHANGED <<nodeState, kmsKeyPossession, clientVetoEnforced>>

KMSVerifyAttestation(msg) ==
    /\ msg \in network
    /\ msg.type = "TPM_QUOTE"
    /\ IF msg.pcr = GoldenPCR
       THEN nodeState' = [nodeState EXCEPT ![msg.node] = "ATTESTED"]
       ELSE nodeState' = [nodeState EXCEPT ![msg.node] = "COMPROMISED"]
    /\ network' = network \ {msg}
    /\ UNCHANGED <<kmsKeyPossession, clientVetoEnforced>>

KMSSendEKMRequest(n, reasonCode) ==
    /\ nodeState[n] = "ATTESTED"
    /\ network' = network \cup {[type |-> "EKM_UNWRAP_REQ", node |-> n, reason |-> reasonCode]}
    /\ UNCHANGED <<nodeState, kmsKeyPossession, clientVetoEnforced>>

ClientEvaluateAccess(msg) ==
    /\ msg \in network
    /\ msg.type = "EKM_UNWRAP_REQ"
    /\ IF msg.reason \in ClientVetoReasons
       THEN /\ clientVetoEnforced' = TRUE
            /\ network' = (network \ {msg}) \cup {[type |-> "EKM_DENIED", node |-> msg.node]}
            /\ UNCHANGED <<nodeState, kmsKeyPossession>>
       ELSE /\ network' = (network \ {msg}) \cup {[type |-> "EKM_KEY_GRANTED", node |-> msg.node]}
            /\ kmsKeyPossession' = TRUE
            /\ UNCHANGED <<nodeState, clientVetoEnforced>>

SovereignVetoSafety ==
    clientVetoEnforced => ~kmsKeyPossession

AttestationIntegrity ==
    \A n \in Nodes : (nodeState[n] /= "ATTESTED") => (~kmsKeyPossession)

=============================================================================
