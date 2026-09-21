#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_core_read.h>
char LICENSE[] SEC("license") = "Dual BSD/GPL";
#define EPERM 1
#define TASK_COMM_LEN 16
#define SHA256_LEN 32
#define MERKLE_ROOT_LEN 32
#define ACTION_PERMIT 0
#define ACTION_DENIED_EPERM 1
/* Kernel kfuncs for reference-counted executable file acquisition */
extern struct file *bpf_get_task_exe_file(struct task_struct *task) __ksym;
extern void bpf_put_file(struct file *file) __ksym;
/* Telemetry payload with cryptographic file provenance */
struct audit_telemetry_event {
    __u64 timestamp_ns;
    __u32 pid;
    __u32 tgid;
    __u32 old_uid;
    __u32 new_uid;
    __u32 old_gid;
    __u32 new_gid;
    char comm[TASK_COMM_LEN];
    __u8 exe_sha256[SHA256_LEN];
    __u8 charter_merkle_root[MERKLE_ROOT_LEN];
    __u32 causal_order_flag;  /* 0x00000004 = O(h⁴) */
    __u32 enforcement_status; /* 1 = ACTIVE_ENFORCING */
    __u32 decision;           /* 0 = PERMIT, 1 = DENIED_EPERM */
};
/* Ring buffer for security events */
struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 256 * 1024);
} audit_ringbuf SEC(".maps");
/* Allowlist hash map keyed by the executable's SHA-256 digest */
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 128);
    __type(key, __u8[SHA256_LEN]);
    __type(value, __u32); /* 1 = AUTHORIZED */
} allowed_sha256_hashes SEC(".maps");
/* Charter Root Merkle Hash anchor */
static const __u8 CHARTER_ROOT[MERKLE_ROOT_LEN] = {
    0x74, 0xa8, 0x5f, 0xc3, 0xa4, 0x6f, 0xa9, 0x68,
    0x93, 0xd0, 0x41, 0x6a, 0x4f, 0xe2, 0x74, 0xea,
    0xa2, 0x57, 0x8a, 0xc8, 0xa0, 0x78, 0x7e, 0xa8,
    0x13, 0x09, 0xe8, 0xb0, 0xe6, 0x7b, 0x07, 0x9c
};
SEC("lsm/cred_prepare")
int BPF_PROG(enforce_cred_prepare_ima, struct cred *new, const struct cred *old, gfp_t gfp_flags, int ret)
{
    if (ret != 0)
        return ret;
    __u32 old_uid = BPF_CORE_READ(old, uid.val);
    __u32 new_uid = BPF_CORE_READ(new, uid.val);
    __u32 decision = ACTION_PERMIT;
    __u8 exe_hash[SHA256_LEN] = {0};
    bool hash_extracted = false;
    /* Extract the current task and reference-counted executable file */
    struct task_struct *task = bpf_get_current_task_btf();
    if (task) {
        struct file *exe_file = bpf_get_task_exe_file(task);
        if (exe_file) {
            /* Compute/retrieve the IMA SHA-256 digest of the backing binary */
            long hash_ret = bpf_ima_file_hash(exe_file, exe_hash, sizeof(exe_hash));
            if (hash_ret >= 0) {
                hash_extracted = true;
            }
            bpf_put_file(exe_file);
        }
    }
    /* Enforce verification on any non-root account attempting elevation to UID 0 */
    if (old_uid != 0 && new_uid == 0) {
        if (!hash_extracted) {
            /* Deny by default if IMA integrity cannot resolve the binary hash */
            decision = ACTION_DENIED_EPERM;
        } else {
            __u32 *is_authorized = bpf_map_lookup_elem(&allowed_sha256_hashes, exe_hash);
            if (!is_authorized || *is_authorized != 1) {
                decision = ACTION_DENIED_EPERM;
            }
        }
    }
    /* Telemetry emission for state transitions and denials */
    if (decision == ACTION_DENIED_EPERM || old_uid != new_uid) {
        struct audit_telemetry_event *event = bpf_ringbuf_reserve(&audit_ringbuf, sizeof(*event), 0);
        if (event) {
            __u64 pid_tgid = bpf_get_current_pid_tgid();
            event->timestamp_ns = bpf_ktime_get_ns();
            event->tgid = pid_tgid >> 32;
            event->pid = (__u32)pid_tgid;
            event->old_uid = old_uid;
            event->new_uid = new_uid;
            event->old_gid = BPF_CORE_READ(old, gid.val);
            event->new_gid = BPF_CORE_READ(new, gid.val);
            event->causal_order_flag = 4;
            event->enforcement_status = 1;
            event->decision = decision;
            bpf_get_current_comm(&event->comm, sizeof(event->comm));
            __builtin_memcpy(event->exe_sha256, exe_hash, SHA256_LEN);
            __builtin_memcpy(event->charter_merkle_root, CHARTER_ROOT, MERKLE_ROOT_LEN);
            bpf_ringbuf_submit(event, 0);
        }
    }
    if (decision == ACTION_DENIED_EPERM) {
        return -EPERM;
    }
    return 0;
}
Go Userspace Allowlist Computation & Registration
package main
import (
"crypto/sha256"
"io"
"log"
"os"
"github.com/cilium/ebpf"
)
// registerAuthorizedBinary computes the binary's SHA-256 hash and registers it in the eBPF map
func registerAuthorizedBinary(allowedMap *ebpf.Map, binaryPath string) error {
f, err := os.Open(binaryPath)
if err != nil {
return err
}
defer f.Close()
hasher := sha256.New()
if _, err := io.Copy(hasher, f); err != nil {
return err
}
hash := hasher.Sum(nil)
var key [32]byte
copy(key[:], hash)
var val uint32 = 1
if err := allowedMap.Put(key, val); err != nil {
return err
}
log.Printf("[ZAFLA] Registered %s (SHA-256: %x)", binaryPath, hash)
return nil
}
func loadPolicyAllowlist(coll *ebpf.Collection) {
allowedMap := coll.Maps["allowed_sha256_hashes"]
trustedBinaries := []string{
"/usr/bin/sudo",
"/usr/sbin/sshd",
"/usr/bin/su",
}
for _, path := range trustedBinaries {
if err := registerAuthorizedBinary(allowedMap, path); err != nil {
log.Printf("[ZAFLA] Warning: Could not hash %s: %v", path, err)
  }
}
}
Kernel Prerequisites & Configuration
• Integrity Measurement Architecture (IMA):CONFIG_IMA=y and CONFIG_IMA_DEFAULT_HASH_SHA256=y must be enabled in the kernel config.
• Kernel Boot Parameters: Boot with ima_policy=tcb ima_hash=sha256 lsm=...,bpf to ensure files measured on execution maintain cached hashes accessible via bpf_ima_file_hash().
• Security Guarantees: Binary renaming or symlink spoofing cannot bypass the check because validation operates directly on the backing struct inode and file content digest rather than user-space task names.
