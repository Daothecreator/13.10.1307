package main
import (
"bytes"
"context"
"encoding/binary"
"encoding/hex"
"errors"
"fmt"
"log"
"os"
"os/signal"
"syscall"
"time"
"github.com/cilium/ebpf"
"github.com/cilium/ebpf/link"
"github.com/cilium/ebpf/ringbuf"
"github.com/cilium/ebpf/rlimit"
)
// AuditTelemetryEvent mirrors the C struct audit_telemetry_event
type AuditTelemetryEvent struct {
TimestampNs       uint64
PID               uint32
TGID              uint32
OldUID            uint32
NewUID            uint32
OldGID            uint32
NewGID            uint32
Comm              [16]byte
CharterMerkleRoot [32]byte
CausalOrderFlag   uint32
EnforcementStatus uint32
}
const bpfObjectFile = "audit_cred_prepare.bpf.o"
func main() {
// Set up OS signal notification for graceful shutdown
ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
defer stop()
// 1. Remove memory lock limits for eBPF operations
if err := rlimit.RemoveMemlock(); err != nil {
log.Fatalf("failed to remove memlock limit: %v", err)
}
// 2. Load the compiled BPF ELF file
spec, err := ebpf.LoadCollectionSpec(bpfObjectFile)
if err != nil {
log.Fatalf("failed to load BPF spec from %s: %v", bpfObjectFile, err)
}
coll, err := ebpf.NewCollection(spec)
if err != nil {
log.Fatalf("failed to instantiate BPF collection: %v", err)
}
defer coll.Close()
// 3. Extract the program and ring buffer map
prog, ok := coll.Programs["audit_cred_prepare"]
if !ok {
log.Fatalf("LSM program 'audit_cred_prepare' not found in ELF")
}
ringbufMap, ok := coll.Maps["audit_ringbuf"]
if !ok {
log.Fatalf("Ring buffer map 'audit_ringbuf' not found in ELF")
}
// 4. Attach to the cred_prepare LSM hook
lsmLink, err := link.AttachLSM(link.LSMOptions{
Program: prog,
})
if err != nil {
log.Fatalf("failed to attach LSM hook (verify CONFIG_BPF_LSM=y): %v", err)
}
defer lsmLink.Close()
log.Println("[ZAFLA] eBPF CO-RE LSM audit hook active on cred_prepare")
// 5. Open ring buffer reader
rd, err := ringbuf.NewReader(ringbufMap)
if err != nil {
log.Fatalf("failed to initialize ring buffer reader: %v", err)
}
defer rd.Close()
// Close ring buffer reader when signal received to break the read loop
go func() {
<-ctx.Done()
rd.Close()
}()
fmt.Println("TIMESTAMP (UTC)             PID     TGID    OLD_UID -> NEW_UID  COMM             MERKLE_ROOT")
fmt.Println("------------------------------------------------------------------------------------------------------------------------")
var event AuditTelemetryEvent
for {
record, err := rd.Read()
if err != nil {
if errors.Is(err, ringbuf.ErrClosed) {
log.Println("[ZAFLA] Signal received, stopping consumer...")
return
}
log.Printf("error reading from ring buffer: %v", err)
continue
}
if err := binary.Read(bytes.NewReader(record.RawSample), binary.LittleEndian, &event); err != nil {
log.Printf("failed to decode event: %v", err)
continue
}
comm := string(bytes.TrimRight(event.Comm[:], "\x00"))
merkleHex := hex.EncodeToString(event.CharterMerkleRoot[:])
timestamp := time.Unix(0, int64(event.TimestampNs)).UTC().Format("2006-01-02 15:04:05.000")
fmt.Printf("%s  %-7d %-7d %-7d -> %-7d %-16s %s... (O(h%d))\n",
timestamp,
event.PID,
event.TGID,
event.OldUID,
event.NewUID,
comm,
merkleHex[:16],
event.CausalOrderFlag,
)
}
}
Execution Requirements
. Kernel Configuration: The host Linux kernel requires CONFIG_BPF_LSM=y and bpf included in the kernel boot parameter lsm=...,bpf.
2. Execution Permissions: The program must execute with CAP_SYS_ADMIN or CAP_BPF + CAP_PERFMON privileges:
go build -o zafla-consumer main.go
sudo ./zafla-consumer           
