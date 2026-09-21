#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_core_read.h>
char LICENSE[] SEC("license") = "Dual BSD/GPL";
#define EPERM 1
#define TASK_COMM_LEN 16
#define MERKLE_ROOT_LEN 32
/* Decision codes */
#define ACTION_PERMIT 0
#define ACTION_DENIED_EPERM 1
/* Telemetry payload committed on credential transition attempt */
struct audit_telemetry_event {
    __u64 timestamp_ns;
    __u32 pid;
    __u32 tgid;
    __u32 old_uid;
    __u32 new_uid;
    __u32 old_gid;
    __u32 new_gid;
    char comm[TASK_COMM_LEN];
    __u8 charter_merkle_root[MERKLE_ROOT_LEN];
    __u32 causal_order_flag;  /* 0x00000004 = O(h⁴) */
    __u32 enforcement_status; /* 1 = ACTIVE_ENFORCING */
    __u32 decision;           /* 0 = PERMIT, 1 = DENIED_EPERM */
};
/* Ring buffer map for userspace telemetry and alerting */
struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 256 * 1024);
} audit_ringbuf SEC(".maps");
/* Allowlist hash map for binaries authorized to escalate to root */
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 64);
    __type(key, char[TASK_COMM_LEN]);
    __type(value, __u32); /* 1 = AUTHORIZED */
} allowed_escalation_comms SEC(".maps");
/* Charter Root Merkle Hash anchor */
static const __u8 CHARTER_ROOT[MERKLE_ROOT_LEN] = {
    0x74, 0xa8, 0x5f, 0xc3, 0xa4, 0x6f, 0xa9, 0x68,
    0x93, 0xd0, 0x41, 0x6a, 0x4f, 0xe2, 0x74, 0xea,
    0xa2, 0x57, 0x8a, 0xc8, 0xa0, 0x78, 0x7e, 0xa8,
    0x13, 0x09, 0xe8, 0xb0, 0xe6, 0x7b, 0x07, 0x9c
};
SEC("lsm/cred_prepare")
int BPF_PROG(enforce_cred_prepare, struct cred *new, const struct cred *old, gfp_t gfp_flags, int ret)
{
    /* Respect prior security decisions in the LSM pipeline */
    if (ret != 0)
        return ret;
    __u32 old_uid = BPF_CORE_READ(old, uid.val);
    __u32 new_uid = BPF_CORE_READ(new, uid.val);
    __u32 decision = ACTION_PERMIT;
    char comm[TASK_COMM_LEN] = {};
    bpf_get_current_comm(&comm, sizeof(comm));
    /* Detect unauthorized transition to root (UID 0) from any non-root account */
    if (old_uid != 0 && new_uid == 0) {
        __u32 *is_allowed = bpf_map_lookup_elem(&allowed_escalation_comms, &comm);
        if (!is_allowed || *is_allowed != 1) {
            decision = ACTION_DENIED_EPERM;
        }
    }
    /* Record telemetry for all blocked attempts or privilege transitions */
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
            __builtin_memcpy(event->comm, comm, sizeof(event->comm));
            __builtin_memcpy(event->charter_merkle_root, CHARTER_ROOT, MERKLE_ROOT_LEN);
            bpf_ringbuf_submit(event, 0);
        }
    }
    /* Enforce active circuit breaker: deny preparation with -EPERM */
    if (decision == ACTION_DENIED_EPERM) {
        return -EPERM;
    }
    return 0;
}
Go Allowlist Population Snippet
To avoid blocking legitimate system tools (such as sudo, sshd, or polkitd), populate the allowed_escalation_comms map from userspace during startup:
allowedMap := coll.Maps["allowed_escalation_comms"]
// Pre-authorized binaries
allowedBinaries := []string{"sudo", "sshd", "su"}
for _, binaryName := range allowedBinaries {
    var key [16]byte
    copy(key[:], binaryName)
    var val uint32 = 1
    if err := allowedMap.Put(key, val); err != nil {
        log.Fatalf("Failed to allowlist %s: %v", binaryName, err)
    }
}
log.Printf("[ZAFLA] Allowlist registered: %v", allowedBinaries)
Enforcement Mechanics
• Intervention Point: When prepare_creds() or copy_creds() calls security_cred_prepare(), returning -EPERM (-1) causes the kernel function to abort and propagate -EPERM back to the initiating syscall (setuid, seteuid, setresuid, execve).
• Zero Bypass: Because the check executes at the LSM layer inside Ring-0, ptrace injection, shell scripts, and unprivileged binaries attempting namespace switching or local exploit elevations are halted before updated credentials attach to struct task_struct.
