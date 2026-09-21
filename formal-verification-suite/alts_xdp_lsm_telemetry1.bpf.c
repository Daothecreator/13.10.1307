#include <vmlinux.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>
#include <bpf/bpf_tracing.h>

#define ETH_P_IP 0x0800
#define IPPROTO_TCP 6
#define ALTS_RECORD_MAGIC 0x414C5453

struct alts_telemetry_event {
    __u64 timestamp_ns;
    __u64 frame_seq;
    __u32 src_ip;
    __u32 dst_ip;
    __u16 src_port;
    __u16 dst_port;
    __u32 payload_len;
    __u8  is_replay;
};

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 1 << 24);
} telemetry_ringbuf SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 65536);
    __type(key, __u64);
    __type(value, __u64);
} alts_channel_state SEC(".maps");

SEC("xdp")
int xdp_alts_inspect(struct xdp_md *ctx) {
    void *data_end = (void *)(long)ctx->data_end;
    void *data = (void *)(long)ctx->data;

    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end) return XDP_PASS;
    if (bpf_ntohs(eth->h_proto) != ETH_P_IP) return XDP_PASS;

    struct iphdr *ip = (void *)(eth + 1);
    if ((void *)(ip + 1) > data_end) return XDP_PASS;
    if (ip->protocol != IPPROTO_TCP) return XDP_PASS;

    struct tcphdr *tcp = (void *)((void *)ip + (ip->ihl * 4));
    if ((void *)(tcp + 1) > data_end) return XDP_PASS;

    __u8 *payload = (void *)((void *)tcp + (tcp->doff * 4));
    if ((void *)(payload + 12) > data_end) return XDP_PASS;

    __u32 magic = *(__u32 *)payload;
    if (magic != bpf_htonl(ALTS_RECORD_MAGIC)) return XDP_PASS;

    __u64 frame_seq = *(__u64 *)(payload + 4);
    frame_seq = bpf_ntohll(frame_seq);

    __u64 channel_id = ((__u64)ip->saddr << 32) | ip->daddr;
    __u64 *highest_seq = bpf_map_lookup_elem(&alts_channel_state, &channel_id);

    __u8 is_replay = 0;
    if (highest_seq) {
        if (frame_seq <= *highest_seq) {
            is_replay = 1;
        } else {
            *highest_seq = frame_seq;
        }
    } else {
        bpf_map_update_elem(&alts_channel_state, &channel_id, &frame_seq, BPF_ANY);
    }

    struct alts_telemetry_event *event = bpf_ringbuf_reserve(&telemetry_ringbuf, sizeof(*event), 0);
    if (!event) return XDP_PASS;

    event->timestamp_ns = bpf_ktime_get_ns();
    event->frame_seq = frame_seq;
    event->src_ip = ip->saddr;
    event->dst_ip = ip->daddr;
    event->src_port = bpf_ntohs(tcp->source);
    event->dst_port = bpf_ntohs(tcp->dest);
    event->payload_len = (__u32)(data_end - (void *)payload);
    event->is_replay = is_replay;

    bpf_ringbuf_submit(event, 0);

    if (is_replay) {
        return XDP_DROP;
    }

    return XDP_PASS;
}

SEC("lsm/bpf")
int BPF_PROG(restrict_bpf_manipulation, int cmd, union bpf_attr *attr, unsigned int size) {
    if (cmd == BPF_PROG_DETACH) {
        return -EPERM;
    }
    return 0;
}

char _license[] SEC("license") = "GPL";
