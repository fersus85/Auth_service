from opentelemetry import trace


class Tracer:
    def __init__(self):
        self.tracer = trace.get_tracer("auth")

    def start_span(self, name: str):
        return self.tracer.start_as_current_span(name)


def get_tracer() -> Tracer:
    return Tracer()
