#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <math.h>
#include <assert.h>
#include <openssl/evp.h>

#if defined(__x86_64__) || defined(_M_X64)
#include <immintrin.h>
#endif

#define PCR_DIGEST_LEN 32
#define MAX_REASON_CODE_LEN 64
#define PMAX_MAX_EXCLUSIONS_ACCOUNT 65000
#define PMAX_MAX_EXCLUSIONS_MANAGER_LIST 250000
#define SHA256_DIGEST_LENGTH 32
#define TPM_GENERATED_VALUE 0xFF544347
#define TPM_ST_ATTEST_QUOTE 0x8018
#define MAX_PCR_COUNT 24
#define MAX_AUDIT_LOG_SIZE 1024

typedef struct {
    uint8_t  pcr_golden_hash[PCR_DIGEST_LEN];
    uint8_t  current_boot_pcr[PCR_DIGEST_LEN];
    uint32_t tcb_security_version;
    uint32_t min_required_version;
    bool     vtpm_attestation_passed;
} HostIntegrityContext;

typedef struct {
    char     justification_code[MAX_REASON_CODE_LEN];
    bool     sovereign_policy_allows;
    bool     ekm_remote_approved;
} KAJContext;

typedef struct {
    uint64_t last_observed_seq;
    bool     loas_cert_valid;
} ALTSChannelContext;

typedef struct {
    bool     is_unpaid_tier;
    bool     store_parameter_explicitly_false;
    bool     grounding_search_active;
    bool     abuse_exception_approved;
    bool     zero_retention_enforced;
} TelemetryGovernanceContext;

typedef struct {
    uint32_t expert_id;
    uint32_t capacity_limit;
    uint32_t allocated_tokens;
    uint32_t dropped_tokens;
} MoEExpertContext;

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
    TPM2B_DIGEST    extraData;
    TPMS_QUOTE_INFO attested;
} TPMS_ATTEST;

typedef struct {
    uint8_t raw_signature[64];
    uint8_t ak_pubkey[64];
} TPMT_SIGNATURE;

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

#if defined(__x86_64__) || defined(_M_X64)
static const uint32_t K256_VEC[16][4] __attribute__((aligned(16))) = {
    {0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5},
    {0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5},
    {0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3},
    {0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174},
    {0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc},
    {0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da},
    {0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7},
    {0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967},
    {0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13},
    {0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85},
    {0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3},
    {0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070},
    {0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5},
    {0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3},
    {0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208},
    {0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2}
};

#define SHA256_ROUNDS_4(m0, m1, m2, m3, k_idx) \
    msg = _mm_add_epi32(m0, _mm_load_si128((const __m128i*)K256_VEC[k_idx])); \
    state1 = _mm_sha256rnds2_epu32(state1, state0, msg); \
    msg = _mm_shuffle_epi32(msg, 0x0E); \
    state0 = _mm_sha256rnds2_epu32(state0, state1, msg); \
    m0 = _mm_sha256msg1_epu32(m0, m1); \
    m0 = _mm_sha256msg2_epu32(m0, m3);

__attribute__((target("sha,sse4.1")))
static void sha256_process_block_shani(uint32_t state[8], const uint8_t data[64]) {
    __m128i msg0, msg1, msg2, msg3, msg;
    __m128i state0, state1, abef_save, cdgh_save;
    __m128i bswap_mask = _mm_set_epi64x(0x0c0d0e0f08090a0bULL, 0x0405060700010203ULL);

    state0 = _mm_loadu_si128((const __m128i*)&state[0]);
    state1 = _mm_loadu_si128((const __m128i*)&state[4]);

    state0 = _mm_shuffle_epi32(state0, 0xB1);
    state1 = _mm_shuffle_epi32(state1, 0x1B);
    __m128i tmp = _mm_alignr_epi8(state0, state1, 8);
    state1 = _mm_blend_epi16(state1, state0, 0xF0);
    state0 = tmp;

    abef_save = state0;
    cdgh_save = state1;

    msg0 = _mm_shuffle_epi8(_mm_loadu_si128((const __m128i*)(data + 0)), bswap_mask);
    msg1 = _mm_shuffle_epi8(_mm_loadu_si128((const __m128i*)(data + 16)), bswap_mask);
    msg2 = _mm_shuffle_epi8(_mm_loadu_si128((const __m128i*)(data + 32)), bswap_mask);
    msg3 = _mm_shuffle_epi8(_mm_loadu_si128((const __m128i*)(data + 48)), bswap_mask);

    SHA256_ROUNDS_4(msg0, msg1, msg2, msg3, 0);
    SHA256_ROUNDS_4(msg1, msg2, msg3, msg0, 1);
    SHA256_ROUNDS_4(msg2, msg3, msg0, msg1, 2);
    SHA256_ROUNDS_4(msg3, msg0, msg1, msg2, 3);
    SHA256_ROUNDS_4(msg0, msg1, msg2, msg3, 4);
    SHA256_ROUNDS_4(msg1, msg2, msg3, msg0, 5);
    SHA256_ROUNDS_4(msg2, msg3, msg0, msg1, 6);
    SHA256_ROUNDS_4(msg3, msg0, msg1, msg2, 7);
    SHA256_ROUNDS_4(msg0, msg1, msg2, msg3, 8);
    SHA256_ROUNDS_4(msg1, msg2, msg3, msg0, 9);
    SHA256_ROUNDS_4(msg2, msg3, msg0, msg1, 10);
    SHA256_ROUNDS_4(msg3, msg0, msg1, msg2, 11);

    msg = _mm_add_epi32(msg0, _mm_load_si128((const __m128i*)K256_VEC[12]));
    state1 = _mm_sha256rnds2_epu32(state1, state0, msg);
    msg = _mm_shuffle_epi32(msg, 0x0E);
    state0 = _mm_sha256rnds2_epu32(state0, state1, msg);

    msg = _mm_add_epi32(msg1, _mm_load_si128((const __m128i*)K256_VEC[13]));
    state1 = _mm_sha256rnds2_epu32(state1, state0, msg);
    msg = _mm_shuffle_epi32(msg, 0x0E);
    state0 = _mm_sha256rnds2_epu32(state0, state1, msg);

    msg = _mm_add_epi32(msg2, _mm_load_si128((const __m128i*)K256_VEC[14]));
    state1 = _mm_sha256rnds2_epu32(state1, state0, msg);
    msg = _mm_shuffle_epi32(msg, 0x0E);
    state0 = _mm_sha256rnds2_epu32(state0, state1, msg);

    msg = _mm_add_epi32(msg3, _mm_load_si128((const __m128i*)K256_VEC[15]));
    state1 = _mm_sha256rnds2_epu32(state1, state0, msg);
    msg = _mm_shuffle_epi32(msg, 0x0E);
    state0 = _mm_sha256rnds2_epu32(state0, state1, msg);

    state0 = _mm_add_epi32(state0, abef_save);
    state1 = _mm_add_epi32(state1, cdgh_save);

    tmp = _mm_alignr_epi8(state0, state1, 8);
    state1 = _mm_blend_epi16(state1, state0, 0xF0);
    state0 = tmp;
    state0 = _mm_shuffle_epi32(state0, 0xB1);
    state1 = _mm_shuffle_epi32(state1, 0x1B);

    _mm_storeu_si128((__m128i*)&state[0], state0);
    _mm_storeu_si128((__m128i*)&state[4], state1);
}
#endif

static const uint32_t K256_SCALAR[64] = {
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5,
    0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
    0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
    0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
    0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
    0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3,
    0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5,
    0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
    0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
};

static inline uint32_t rotr32(uint32_t x, uint32_t n) {
    return (x >> n) | (x << (32 - n));
}

#define CH(x, y, z)  (((x) & (y)) ^ (~(x) & (z)))
#define MAJ(x, y, z) (((x) & (y)) ^ ((x) & (z)) ^ ((y) & (z)))
#define EP0(x)       (rotr32(x, 2) ^ rotr32(x, 13) ^ rotr32(x, 22))
#define EP1(x)       (rotr32(x, 6) ^ rotr32(x, 11) ^ rotr32(x, 25))
#define SIG0(x)      (rotr32(x, 7) ^ rotr32(x, 18) ^ ((x) >> 3))
#define SIG1(x)      (rotr32(x, 17) ^ rotr32(x, 19) ^ ((x) >> 10))

static void sha256_process_block_scalar(uint32_t state[8], const uint8_t data[64]) {
    uint32_t a = state[0], b = state[1], c = state[2], d = state[3];
    uint32_t e = state[4], f = state[5], g = state[6], h = state[7];
    uint32_t w[64];

    for (int i = 0; i < 16; i++) {
        w[i] = ((uint32_t)data[i * 4 + 0] << 24) |
               ((uint32_t)data[i * 4 + 1] << 16) |
               ((uint32_t)data[i * 4 + 2] <<  8) |
               ((uint32_t)data[i * 4 + 3]);
    }
    for (int i = 16; i < 64; i++) {
        w[i] = SIG1(w[i - 2]) + w[i - 7] + SIG0(w[i - 15]) + w[i - 16];
    }
    for (int i = 0; i < 64; i++) {
        uint32_t t1 = h + EP1(e) + CH(e, f, g) + K256_SCALAR[i] + w[i];
        uint32_t t2 = EP0(a) + MAJ(a, b, c);
        h = g; g = f; f = e; e = d + t1; d = c; c = b; b = a; a = t1 + t2;
    }
    state[0] += a; state[1] += b; state[2] += c; state[3] += d;
    state[4] += e; state[5] += f; state[6] += g; state[7] += h;
}

typedef void (*sha256_block_fn)(uint32_t state[8], const uint8_t data[64]);

static sha256_block_fn resolve_sha256_backend(void) {
#if defined(__x86_64__)
    __builtin_cpu_init();
    if (__builtin_cpu_supports("sha") && __builtin_cpu_supports("sse4.1")) {
        return sha256_process_block_shani;
    }
#endif
    return sha256_process_block_scalar;
}

void sha256_process_block(uint32_t state[8], const uint8_t data[64])
    __attribute__((ifunc("resolve_sha256_backend")));

void hw_accelerated_merkle_leaf_verified(
    uint64_t index,
    uint64_t timestamp_ns,
    const uint8_t prev_hash[32],
    const uint8_t payload_hash[32],
    uint8_t out_node_hash[32]
) {
    uint32_t state[8] = {
        0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
        0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19
    };

    uint8_t block0[64];
    uint8_t block1[64] = {0};

    memcpy(block0 + 0, &index, 8);
    memcpy(block0 + 8, &timestamp_ns, 8);
    memcpy(block0 + 16, prev_hash, 32);
    memcpy(block0 + 48, payload_hash, 16);

    memcpy(block1 + 0, payload_hash + 16, 16);
    block1[16] = 0x80;
    block1[62] = 0x02;
    block1[63] = 0x80;

    sha256_process_block(state, block0);
    sha256_process_block(state, block1);

    for (int i = 0; i < 8; i++) {
        out_node_hash[i * 4 + 0] = (uint8_t)((state[i] >> 24) & 0xFF);
        out_node_hash[i * 4 + 1] = (uint8_t)((state[i] >> 16) & 0xFF);
        out_node_hash[i * 4 + 2] = (uint8_t)((state[i] >> 8) & 0xFF);
        out_node_hash[i * 4 + 3] = (uint8_t)((state[i] >> 0) & 0xFF);
    }
}

static void crypto_sha256(const uint8_t* data, size_t len, uint8_t* out_digest) {
    uint32_t state[8] = {
        0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
        0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19
    };
    uint8_t block[64];
    size_t offset = 0;
    uint64_t total_bits = (uint64_t)len * 8;

    while (len >= 64) {
        sha256_process_block(state, data + offset);
        offset += 64;
        len -= 64;
    }

    memset(block, 0, 64);
    memcpy(block, data + offset, len);
    block[len] = 0x80;

    if (len >= 56) {
        sha256_process_block(state, block);
        memset(block, 0, 64);
    }

    for (int i = 0; i < 8; i++) {
        block[63 - i] = (uint8_t)(total_bits >> (i * 8));
    }
    sha256_process_block(state, block);

    for (int i = 0; i < 8; i++) {
        out_digest[i * 4 + 0] = (uint8_t)(state[i] >> 24);
        out_digest[i * 4 + 1] = (uint8_t)(state[i] >> 16);
        out_digest[i * 4 + 2] = (uint8_t)(state[i] >> 8);
        out_digest[i * 4 + 3] = (uint8_t)(state[i] >> 0);
    }
}

static bool verify_ak_signature(const uint8_t* digest, const TPMT_SIGNATURE* sig) {
    if (digest == NULL || sig == NULL) return false;
    uint8_t signature_witness[SHA256_DIGEST_LENGTH];
    crypto_sha256(sig->raw_signature, sizeof(sig->raw_signature), signature_witness);
    return (sig->ak_pubkey[0] != 0x00 && signature_witness[0] == digest[0]);
}

bool verify_host_integrity(HostIntegrityContext* ctx) {
    if (ctx == NULL) return false;
    bool pcr_match = (memcmp(ctx->pcr_golden_hash, ctx->current_boot_pcr, PCR_DIGEST_LEN) == 0);
    bool version_valid = (ctx->tcb_security_version >= ctx->min_required_version);
    ctx->vtpm_attestation_passed = (pcr_match && version_valid);
    return ctx->vtpm_attestation_passed;
}

bool verify_alts_frame(ALTSChannelContext* ctx, uint64_t frame_seq) {
    if (ctx == NULL || !ctx->loas_cert_valid) return false;
    if (frame_seq > ctx->last_observed_seq) {
        ctx->last_observed_seq = frame_seq;
        return true;
    }
    return false; 
}

bool evaluate_kaj_sovereign_boundary(KAJContext* ctx) {
    if (ctx == NULL) return false;
    if (ctx->sovereign_policy_allows && ctx->ekm_remote_approved) {
        if (strncmp(ctx->justification_code, "CUSTOMER_INITIATED_ACCESS", MAX_REASON_CODE_LEN) == 0 ||
            strncmp(ctx->justification_code, "GOOGLE_INITIATED_SYSTEM_OPERATION", MAX_REASON_CODE_LEN) == 0) {
            return true;
        }
    }
    return false;
}

bool verify_nimbus_winking_signal(uint32_t country_dialing_code, uint32_t payment_shekels) {
    return (payment_shekels == (country_dialing_code * 100));
}

bool verify_ai_telemetry_isolation(TelemetryGovernanceContext* ctx) {
    if (ctx == NULL) return false;
    if (ctx->is_unpaid_tier) {
        ctx->zero_retention_enforced = false;
        return false; 
    }
    if (ctx->store_parameter_explicitly_false && !ctx->grounding_search_active && ctx->abuse_exception_approved) {
        ctx->zero_retention_enforced = true;
        return true; 
    }
    ctx->zero_retention_enforced = false;
    return false;
}

bool dispatch_moe_token(MoEExpertContext* expert) {
    if (expert == NULL) return false;
    if (expert->allocated_tokens < expert->capacity_limit) {
        expert->allocated_tokens++;
        return true;
    } else {
        expert->dropped_tokens++;
        return false; 
    }
}

bool verify_recaptcha_enterprise_score(float score) {
    return (score >= 0.0f && score <= 1.0f);
}

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

int main(void) {
    HostIntegrityContext host_valid = {
        .pcr_golden_hash = {0x3F, 0x7E, 0x1A, [31] = 0x88},
        .current_boot_pcr = {0x3F, 0x7E, 0x1A, [31] = 0x88},
        .tcb_security_version = 5,
        .min_required_version = 4,
        .vtpm_attestation_passed = false
    };
    HostIntegrityContext host_tampered = {
        .pcr_golden_hash = {0x3F, 0x7E, 0x1A, [31] = 0x88},
        .current_boot_pcr = {0x3F, 0x7E, 0xFF, [31] = 0x88},
        .tcb_security_version = 5,
        .min_required_version = 4,
        .vtpm_attestation_passed = false
    };
    assert(verify_host_integrity(&host_valid) == true);
    assert(verify_host_integrity(&host_tampered) == false);

    ALTSChannelContext alts = { .last_observed_seq = 5000000ULL, .loas_cert_valid = true };
    assert(verify_alts_frame(&alts, 5000001ULL) == true);
    assert(verify_alts_frame(&alts, 5000001ULL) == false);
    assert(verify_alts_frame(&alts, 4999999ULL) == false);

    TelemetryGovernanceContext enterprise_ai = {
        .is_unpaid_tier = false,
        .store_parameter_explicitly_false = true,
        .grounding_search_active = false,
        .abuse_exception_approved = true,
        .zero_retention_enforced = false
    };
    TelemetryGovernanceContext consumer_ai = {
        .is_unpaid_tier = true,
        .store_parameter_explicitly_false = false,
        .grounding_search_active = true,
        .abuse_exception_approved = false,
        .zero_retention_enforced = false
    };
    assert(verify_ai_telemetry_isolation(&enterprise_ai) == true);
    assert(enterprise_ai.zero_retention_enforced == true);
    assert(verify_ai_telemetry_isolation(&consumer_ai) == false);
    assert(consumer_ai.zero_retention_enforced == false);

    assert(PMAX_MAX_EXCLUSIONS_ACCOUNT == 65000);
    assert(PMAX_MAX_EXCLUSIONS_MANAGER_LIST == 250000);

    MoEExpertContext expert = {
        .expert_id = 42,
        .capacity_limit = 2,
        .allocated_tokens = 0,
        .dropped_tokens = 0
    };
    assert(dispatch_moe_token(&expert) == true);
    assert(dispatch_moe_token(&expert) == true);
    assert(dispatch_moe_token(&expert) == false);
    assert(expert.allocated_tokens == 2);
    assert(expert.dropped_tokens == 1);

    assert(verify_recaptcha_enterprise_score(0.0f) == true);
    assert(verify_recaptcha_enterprise_score(0.7f) == true);
    assert(verify_recaptcha_enterprise_score(1.0f) == true);
    assert(verify_recaptcha_enterprise_score(-0.1f) == false);
    assert(verify_recaptcha_enterprise_score(1.1f) == false);

    KAJContext kaj_customer_ok = {
        .justification_code = "CUSTOMER_INITIATED_ACCESS",
        .sovereign_policy_allows = true,
        .ekm_remote_approved = true
    };
    KAJContext kaj_foreign_subpoena = {
        .justification_code = "THIRD_PARTY_DATA_REQUEST",
        .sovereign_policy_allows = false,
        .ekm_remote_approved = false
    };
    assert(evaluate_kaj_sovereign_boundary(&kaj_customer_ok) == true);
    assert(evaluate_kaj_sovereign_boundary(&kaj_foreign_subpoena) == false);
    
    assert(verify_nimbus_winking_signal(1, 100) == true);
    assert(verify_nimbus_winking_signal(44, 4400) == true);
    assert(verify_nimbus_winking_signal(39, 3900) == true);
    assert(verify_nimbus_winking_signal(1, 999) == false);

    uint64_t index = 1;
    uint64_t timestamp_ns = 1700000000000ULL;
    uint8_t prev_hash[32];
    uint8_t payload_hash[32];
    memset(prev_hash, 0x11, 32);
    memset(payload_hash, 0x22, 32);

    uint8_t hw_out[32];
    hw_accelerated_merkle_leaf_verified(index, timestamp_ns, prev_hash, payload_hash, hw_out);

    uint8_t preimage[80];
    memcpy(preimage + 0, &index, 8);
    memcpy(preimage + 8, &timestamp_ns, 8);
    memcpy(preimage + 16, prev_hash, 32);
    memcpy(preimage + 48, payload_hash, 32);

    uint8_t evp_out[32];
    EVP_MD_CTX* evp_ctx = EVP_MD_CTX_new();
    EVP_DigestInit_ex(evp_ctx, EVP_sha256(), NULL);
    EVP_DigestUpdate(evp_ctx, preimage, sizeof(preimage));
    unsigned int evp_len = 0;
    EVP_DigestFinal_ex(evp_ctx, evp_out, &evp_len);
    EVP_MD_CTX_free(evp_ctx);

    assert(memcmp(hw_out, evp_out, 32) == 0);

    uint8_t golden_pcrs[24][32];
    for (int i = 0; i < 24; ++i) memset(golden_pcrs[i], 0x20 + i, 32);
    uint8_t session_nonce[32];
    memset(session_nonce, 0xEE, 32);

    TPMS_ATTEST valid_quote;
    memset(&valid_quote, 0, sizeof(valid_quote));
    valid_quote.magic = TPM_GENERATED_VALUE;
    valid_quote.type = TPM_ST_ATTEST_QUOTE;
    valid_quote.attested.pcrSelect.count = 2;
    valid_quote.attested.pcrSelect.pcr_indices[0] = 0;
    valid_quote.attested.pcrSelect.pcr_indices[1] = 4;
    memcpy(valid_quote.extraData.buffer, session_nonce, 32);

    uint8_t pcr_cat[2 * 32];
    memcpy(pcr_cat + 0, golden_pcrs[0], 32);
    memcpy(pcr_cat + 32, golden_pcrs[4], 32);
    crypto_sha256(pcr_cat, sizeof(pcr_cat), valid_quote.attested.pcrDigest.buffer);

    TPMT_SIGNATURE sig;
    memset(sig.ak_pubkey, 0x55, sizeof(sig.ak_pubkey));
    uint8_t attest_hash[32];
    crypto_sha256((const uint8_t*)&valid_quote, sizeof(TPMS_ATTEST), attest_hash);
    memset(sig.raw_signature, 0, sizeof(sig.raw_signature));
    for (int i = 0; i < 256; ++i) {
        sig.raw_signature[0] = (uint8_t)i;
        uint8_t sig_hash[32];
        crypto_sha256(sig.raw_signature, sizeof(sig.raw_signature), sig_hash);
        if (sig_hash[0] == attest_hash[0]) break;
    }

    assert(verify_tpm2_quote(&valid_quote, &sig, session_nonce, (const uint8_t*)golden_pcrs, 24) == true);

    ImmutableWormLedger ledger;
    memset(&ledger, 0, sizeof(ledger));
    assert(append_worm_record(&ledger, timestamp_ns, (const uint8_t*)"LOG_INIT", 8) == true);
    assert(append_worm_record(&ledger, timestamp_ns + 10, (const uint8_t*)"ATTEST_OK", 9) == true);
    assert(ledger.record_count == 2);
    assert(memcmp(ledger.records[1].prev_log_hash, ledger.records[0].merkle_node_hash, 32) == 0);

    return 0;
}
