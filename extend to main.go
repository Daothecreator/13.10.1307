go get go.opentelemetry.io/otel/exporters/otlp/otlptrace \
       go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc \
       google.golang.org/grpc
Updated OpenTelemetry OTLP/gRPC Initialization (main.go)
package main
import (
"bytes"
"context"
"encoding/binary"
"encoding/hex"
"errors"
"fmt"
"log"
"net/http"
"os"
"os/signal"
"strconv"
"syscall"
"time"
"github.com/cilium/ebpf"
"github.com/cilium/ebpf/link"
"github.com/cilium/ebpf/ringbuf"
"github.com/cilium/ebpf/rlimit"
"github.com/prometheus/client_golang/prometheus"
"github.com/prometheus/client_golang/prometheus/promauto"
"github.com/prometheus/client_golang/prometheus/promhttp"
"go.opentelemetry.io/otel"
"go.opentelemetry.io/otel/attribute"
"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
"go.opentelemetry.io/otel/sdk/resource"
sdktrace "go.opentelemetry.io/otel/sdk/trace"
semconv "go.opentelemetry.io/otel/semconv/v1.26.0"
oteltrace "go.opentelemetry.io/otel/trace"
"google.golang.org/grpc"
"google.golang.org/grpc/credentials/insecure"
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
const (
bpfObjectFile = "audit_cred_prepare.bpf.o"
metricsPort   = ":2112"
)
var (
credEventsTotal = promauto.NewCounterVec(
prometheus.CounterOpts{
Namespace: "zafla",
Subsystem: "lsm",
Name:      "cred_prepare_events_total",
Help:      "Total number of cred_prepare state transitions observed by the eBPF LSM hook.",
},
[]string{"comm", "old_uid", "new_uid", "causal_order"},
)
privilegeTransitionsTotal = promauto.NewCounterVec(
prometheus.CounterOpts{
Namespace: "zafla",
Subsystem: "lsm",
Name:      "privilege_transitions_total",
Help:      "Tracks elevation (non-root -> root) and dropping of privileges.",
},
[]string{"transition_type", "comm"},
)
)
// initOpenTelemetry sets up an OTLP gRPC trace exporter directed at an OpenTelemetry Collector
func initOpenTelemetry(ctx context.Context) (*sdktrace.TracerProvider, error) {
collectorEndpoint := os.Getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
if collectorEndpoint == "" {
collectorEndpoint = "localhost:4317"
}
// Configure the OTLP gRPC exporter
exporter, err := otlptracegrpc.New(
ctx,
otlptracegrpc.WithEndpoint(collectorEndpoint),
otlptracegrpc.WithTLSCredentials(insecure.NewCredentials()),
otlptracegrpc.WithDialOption(grpc.WithBlock()),
otlptracegrpc.WithTimeout(5*time.Second),
)
if err != nil {
return nil, fmt.Errorf("failed to create OTLP gRPC trace exporter: %w", err)
}
res, err := resource.New(ctx,
resource.WithAttributes(
semconv.ServiceNameKey.String("zafla-kernel-telemetry"),
semconv.ServiceVersionKey.String("1.0.0"),
attribute.String("policy.id", "FLA-POL-2026-ZA01"),
attribute.String("telemetry.layer", "Ring-0/LSM"),
),
)
if err != nil {
return nil, fmt.Errorf("failed to create resource: %w", err)
}
// Batch spans before transmission to the collector
bsp := sdktrace.NewBatchSpanProcessor(exporter,
sdktrace.WithBatchTimeout(1*time.Second),
sdktrace.WithMaxExportBatchSize(512),
)
tp := sdktrace.NewTracerProvider(
sdktrace.WithSampler(sdktrace.AlwaysSample()),
sdktrace.WithResource(res),
sdktrace.WithSpanProcessor(bsp),
)
otel.SetTracerProvider(tp)
return tp, nil
}
func main() {
ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
defer stop()
// 1. Initialize OTLP gRPC Tracer Provider
tp, err := initOpenTelemetry(ctx)
if err != nil {
log.Fatalf("[ZAFLA] OTel OTLP gRPC initialization error: %v", err)
}
defer func() {
shutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
defer cancel()
if err := tp.Shutdown(shutdownCtx); err != nil {
log.Printf("[ZAFLA] Error shutting down TracerProvider: %v", err)
}
}()
tracer := otel.Tracer("zafla-cred-tracer")
// 2. Start Prometheus Metrics HTTP Server
http.Handle("/metrics", promhttp.Handler())
metricsServer := &http.Server{Addr: metricsPort}
go func() {
log.Printf("[ZAFLA] Prometheus metrics endpoint running on http://localhost%s/metrics", metricsPort)
if err := metricsServer.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
log.Fatalf("[ZAFLA] Prometheus HTTP server failed: %v", err)
}
}()
defer metricsServer.Shutdown(context.Background())
// 3. Remove memlock limits
if err := rlimit.RemoveMemlock(); err != nil {
log.Fatalf("[ZAFLA] Failed to remove memlock limit: %v", err)
}
// 4. Load BPF program and maps
spec, err := ebpf.LoadCollectionSpec(bpfObjectFile)
if err != nil {
log.Fatalf("[ZAFLA] Failed to load BPF spec: %v", err)
}
coll, err := ebpf.NewCollection(spec)
if err != nil {
log.Fatalf("[ZAFLA] Failed to instantiate BPF collection: %v", err)
}
defer coll.Close()
prog, ok := coll.Programs["audit_cred_prepare"]
if !ok {
log.Fatalf("[ZAFLA] LSM program 'audit_cred_prepare' not found")
}
ringbufMap, ok := coll.Maps["audit_ringbuf"]
if !ok {
log.Fatalf("[ZAFLA] Ring buffer map 'audit_ringbuf' not found")
}
lsmLink, err := link.AttachLSM(link.LSMOptions{Program: prog})
if err != nil {
log.Fatalf("[ZAFLA] Failed to attach LSM hook: %v", err)
}
defer lsmLink.Close()
log.Println("[ZAFLA] LSM hook active. Forwarding traces to OTLP Collector over gRPC...")
// 5. Open Ring Buffer Reader
rd, err := ringbuf.NewReader(ringbufMap)
if err != nil {
log.Fatalf("[ZAFLA] Failed to initialize ring buffer reader: %v", err)
}
defer rd.Close()
go func() {
<-ctx.Done()
rd.Close()
}()
var event AuditTelemetryEvent
for {
record, err := rd.Read()
if err != nil {
if errors.Is(err, ringbuf.ErrClosed) {
log.Println("[ZAFLA] Shutting down ring buffer reader...")
return
}
log.Printf("[ZAFLA] Ring buffer read error: %v", err)
continue
}
if err := binary.Read(bytes.NewReader(record.RawSample), binary.LittleEndian, &event); err != nil {
log.Printf("[ZAFLA] Event decoding failed: %v", err)
continue
}
comm := string(bytes.TrimRight(event.Comm[:], "\x00"))
merkleHex := hex.EncodeToString(event.CharterMerkleRoot[:])
eventTime := time.Unix(0, int64(event.TimestampNs)).UTC()
causalOrderStr := fmt.Sprintf("O(h%d)", event.CausalOrderFlag)
// Record Prometheus Metrics
credEventsTotal.WithLabelValues(
comm,
strconv.FormatUint(uint64(event.OldUID), 10),
strconv.FormatUint(uint64(event.NewUID), 10),
causalOrderStr,
).Inc()
if event.OldUID != 0 && event.NewUID == 0 {
privilegeTransitionsTotal.WithLabelValues("escalation_to_root", comm).Inc()
} else if event.OldUID == 0 && event.NewUID != 0 {
privilegeTransitionsTotal.WithLabelValues("drop_from_root", comm).Inc()
}
// Emit OTLP Span to gRPC Batch Processor
_, span := tracer.Start(ctx, "cred_prepare_transition",
oteltrace.WithTimestamp(eventTime),
oteltrace.WithAttributes(
attribute.Int64("audit.pid", int64(event.PID)),
attribute.Int64("audit.tgid", int64(event.TGID)),
attribute.Int64("audit.old_uid", int64(event.OldUID)),
attribute.Int64("audit.new_uid", int64(event.NewUID)),
attribute.Int64("audit.old_gid", int64(event.OldGID)),
attribute.Int64("audit.new_gid", int64(event.NewGID)),
attribute.String("audit.comm", comm),
attribute.String("audit.merkle_root", merkleHex),
attribute.String("audit.causal_order", causalOrderStr),
attribute.Int64("audit.enforcement_status", int64(event.EnforcementStatus)),
),
)
span.End(oteltrace.WithTimestamp(time.Now().UTC()))
}
}  
