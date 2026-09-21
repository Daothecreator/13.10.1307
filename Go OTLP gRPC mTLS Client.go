package main
import (
"context"
"crypto/tls"
"crypto/x509"
"fmt"
"os"
"time"
"go.opentelemetry.io/otel"
"go.opentelemetry.io/otel/attribute"
"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
"go.opentelemetry.io/otel/sdk/resource"
sdktrace "go.opentelemetry.io/otel/sdk/trace"
semconv "go.opentelemetry.io/otel/semconv/v1.26.0"
"google.golang.org/grpc/credentials"
)
// loadMTLSCredentials reads CA, client certificate, and private key from disk
func loadMTLSCredentials(caCertPath, clientCertPath, clientKeyPath, serverNameOverride string) (credentials.TransportCredentials, error) {
// 1. Load CA certificate to verify the OTel Collector
caCert, err := os.ReadFile(caCertPath)
if err != nil {
return nil, fmt.Errorf("failed to read CA certificate: %w", err)
}
caPool := x509.NewCertPool()
if !caPool.AppendCertsFromPEM(caCert) {
return nil, fmt.Errorf("failed to append CA certificate to pool")
}
// 2. Load client certificate and private key for mutual authentication
clientCert, err := tls.LoadX509KeyPair(clientCertPath, clientKeyPath)
if err != nil {
return nil, fmt.Errorf("failed to load client keypair: %w", err)
}
// 3. Assemble TLS Configuration
tlsConfig := &tls.Config{
Certificates: []tls.Certificate{clientCert},
RootCAs:      caPool,
ServerName:   serverNameOverride, // e.g., "otel-collector.zafla.internal"
MinVersion:   tls.VersionTLS13,   // Enforce TLS 1.3
}
return credentials.NewTLS(tlsConfig), nil
}
// initOpenTelemetry configures the OTLP trace exporter with mTLS over gRPC
func initOpenTelemetry(ctx context.Context) (*sdktrace.TracerProvider, error) {
collectorEndpoint := os.Getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
if collectorEndpoint == "" {
collectorEndpoint = "otel-collector.zafla.internal:4317"
}
caPath := os.Getenv("OTEL_EXPORTER_OTLP_CERTIFICATE")
clientCertPath := os.Getenv("OTEL_EXPORTER_OTLP_CLIENT_CERTIFICATE")
clientKeyPath := os.Getenv("OTEL_EXPORTER_OTLP_CLIENT_KEY")
serverName := os.Getenv("OTEL_EXPORTER_OTLP_SERVER_NAME")
if caPath == "" || clientCertPath == "" || clientKeyPath == "" {
return nil, fmt.Errorf("missing required mTLS certificate environment variables")
}
tlsCreds, err := loadMTLSCredentials(caPath, clientCertPath, clientKeyPath, serverName)
if err != nil {
return nil, fmt.Errorf("failed to configure mTLS transport credentials: %w", err)
}
// Configure gRPC exporter with mutual TLS
exporter, err := otlptracegrpc.New(
ctx,
otlptracegrpc.WithEndpoint(collectorEndpoint),
otlptracegrpc.WithTLSCredentials(tlsCreds),
otlptracegrpc.WithTimeout(5*time.Second),
)
if err != nil {
return nil, fmt.Errorf("failed to create secure OTLP gRPC trace exporter: %w", err)
}
res, err := resource.New(ctx,
resource.WithAttributes(
semconv.ServiceNameKey.String("zafla-kernel-telemetry"),
semconv.ServiceVersionKey.String("1.0.0"),
attribute.String("policy.id", "FLA-POL-2026-ZA01"),
attribute.String("telemetry.layer", "Ring-0/LSM"),
attribute.String("telemetry.transport", "gRPC/mTLS-v1.3"),
),
)
if err != nil {
return nil, fmt.Errorf("failed to initialize resource: %w", err)
}
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
