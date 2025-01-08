from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from core.config import settings


def configure_tracer() -> None:
    resource = Resource(attributes={SERVICE_NAME: settings.PROJECT_NAME})
    trace_provider = TracerProvider(resource=resource)
    endpoint = f"http://{settings.jaeger.HOST}:{settings.jaeger.PORT}"
    processor = BatchSpanProcessor(
        OTLPSpanExporter(endpoint=endpoint, insecure=True)
    )
    trace_provider.add_span_processor(processor)
    trace.set_tracer_provider(trace_provider)
