from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def configure_tracer() -> None:
    resource = Resource(attributes={SERVICE_NAME: "auth"})
    trace_provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(
        OTLPSpanExporter(endpoint="http://jaeger:4317", insecure=True)
    )
    trace_provider.add_span_processor(processor)
    trace.set_tracer_provider(trace_provider)
