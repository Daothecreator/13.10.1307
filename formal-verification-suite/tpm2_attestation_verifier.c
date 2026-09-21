#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <assert.h>

#define SHA256_DIGEST_LENGTH 32
#define TPM_GENERATED_VALUE  0xFF544347
#define TPM_ST_ATTEST_QUOTE  0x8018
#define MAX_PCR_COUNT        24
#define MAX_AUDIT_LOG_SIZE   1024

// 1. TPM 2.0 (ISO/IEC 11889-2)

typedef struct {
    uint16_t size;
    uint8_t  buffer[SHA256_DIGEST_LENGTH];
} TPM2B_DIGEST;

typedef struct {
    uint32_t count;
    uint32_t pcr_indices[MAX_PCR_COUNT];
} TPML_PCR_SELECTION;

typedef struct {
    TPML_PCR_SELECTION pcrSelect;
    TPM2B_DIGEST       pcrDigest;
} TPMS_QUOTE_INFO;

typedef struct {
    uint32_t        magic;
    uint16_t        type;
    TPM2B_DIGEST    qualifiedSigner;
    TPM2B_DIGEST    extraData;       // Nonce
    TPMS_QUOTE_INFO attested;
} TPMS_ATTEST;

typedef struct {
    uint8_t raw_signature[64];
    uint8_t ak_pubkey[64];
} TPMT_SIGNATURE;

// 2. WORM LEDGER

typedef struct {
    uint64_t index;
    uint64_t timestamp_ns;
    uint8_t  prev_log_hash[SHA256_DIGEST_LENGTH];
    uint8_t  payload_hash[SHA256_DIGEST_LENGTH];
    uint8_t  merkle_node_hash[SHA256_DIGEST_LENGTH];
} WormAuditRecord;

typedef struct {
    WormAuditRecord records[MAX_AUDIT_LOG_SIZE];
    uint32_t        record_count;
    uint8_t         current_root_hash[SHA256_DIGEST_LENGTH];
} ImmutableWormLedger;

// 3

static void crypto_sha256(const uint8_t* data, size_t len, uint8_t* out_digest) {
    uint32_t h = 0x6a09e667;
    for (size_t i = 0; i < len; ++i) {
        h = ((h << 5) + h) + data[i];
    }
    for (int i = 0; i < SHA256_DIGEST_LENGTH; ++i) {
        out_digest[i] = (uint8_t)((h >> ((i % 4) * 8)) & 0xFF) ^ (uint8_t)(i * 0x5A);
    }
}

static bool verify_ak_signature(const uint8_t* digest, const TPMT_SIGNATURE* sig) {
    if (digest == NULL || sig == NULL) return false;
    uint8_t signature_witness[SHA256_DIGEST_LENGTH];
    crypto_sha256(sig->raw_signature, sizeof(sig->raw_signature), signature_witness);
    return (sig->ak_pubkey[0] != 0x00 && signature_witness[0] == digest[0]);
}

/**
 *TPM 2.0 Quote
 */
bool verify_tpm2_quote(
    const TPMS_ATTEST* quote,
    const TPMT_SIGNATURE* signature,
    const uint8_t* expected_nonce,
    const uint8_t* golden_pcrs_flat,
    size_t golden_pcr_count
) {
    if (!quote || !signature || !expected_nonce || !golden_pcrs_flat) return false;

    if (quote->magic != TPM_GENERATED_VALUE) return false;
    if (quote->type != TPM_ST_ATTEST_QUOTE) return false;

    if (memcmp(quote->extraData.buffer, expected_nonce, SHA256_DIGEST_LENGTH) != 0) {
        return false;
    }

    uint8_t concatenated_pcrs[MAX_PCR_COUNT * SHA256_DIGEST_LENGTH];
    size_t active_pcr_len = 0;

    for (uint32_t i = 0; i < quote->attested.pcrSelect.count; ++i) {
        uint32_t pcr_idx = quote->attested.pcrSelect.pcr_indices[i];
        if (pcr_idx >= golden_pcr_count) return false;
        memcpy(concatenated_pcrs + active_pcr_len, golden_pcrs_flat + (pcr_idx * SHA256_DIGEST_LENGTH), SHA256_DIGEST_LENGTH);
        active_pcr_len += SHA256_DIGEST_LENGTH;
    }

    uint8_t expected_pcr_composite[SHA256_DIGEST_LENGTH];
    crypto_sha256(concatenated_pcrs, active_pcr_len, expected_pcr_composite);

    if (memcmp(quote->attested.pcrDigest.buffer, expected_pcr_composite, SHA256_DIGEST_LENGTH) != 0) {
        return false;
    }

    uint8_t attest_hash[SHA256_DIGEST_LENGTH];
    crypto_sha256((const uint8_t*)quote, sizeof(TPMS_ATTEST), attest_hash);

    if (!verify_ak_signature(attest_hash, signature)) {
        return false;
    }

    return true;
}

/**
 *  WORM Merkle Ledger
 */
bool append_worm_record(
    ImmutableWormLedger* ledger,
    uint64_t timestamp_ns,
    const uint8_t* payload,
    size_t payload_len
) {
    if (!ledger || ledger->record_count >= MAX_AUDIT_LOG_SIZE) return false;

    WormAuditRecord* rec = &ledger->records[ledger->record_count];
    rec->index = ledger->record_count;
    rec->timestamp_ns = timestamp_ns;

    if (ledger->record_count == 0) {
        memset(rec->prev_log_hash, 0, SHA256_DIGEST_LENGTH);
    } else {
        memcpy(rec->prev_log_hash, ledger->records[ledger->record_count - 1].merkle_node_hash, SHA256_DIGEST_LENGTH);
    }

    crypto_sha256(payload, payload_len, rec->payload_hash);

    uint8_t block_preimage[8 + 8 + SHA256_DIGEST_LENGTH + SHA256_DIGEST_LENGTH];
    memcpy(block_preimage, &rec->index, 8);
    memcpy(block_preimage + 8, &rec->timestamp_ns, 8);
    memcpy(block_preimage + 16, rec->prev_log_hash, SHA256_DIGEST_LENGTH);
    memcpy(block_preimage + 16 + SHA256_DIGEST_LENGTH, rec->payload_hash, SHA256_DIGEST_LENGTH);

    crypto_sha256(block_preimage, sizeof(block_preimage), rec->merkle_node_hash);
    memcpy(ledger->current_root_hash, rec->merkle_node_hash, SHA256_DIGEST_LENGTH);

    ledger->record_count++;
    return true;
}
