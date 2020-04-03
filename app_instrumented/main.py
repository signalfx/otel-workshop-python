import requests
from flask import Flask, request
from opentelemetry import trace
from opentelemetry import propagators, trace
from opentelemetry.ext.otcollector.trace_exporter import CollectorSpanExporter
from opentelemetry.ext import http_requests
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchExportSpanProcessor
from opentelemetry.ext.wsgi import OpenTelemetryMiddleware
from opentelemetry.ext.zipkin import ZipkinSpanExporter


# configure tracer and exporter
#exporter = CollectorSpanExporter(
#    service_name="py-service",
#    endpoint="localhost:55678",
#)
exporter = ZipkinSpanExporter(
    service_name="py-service",
    # optional:
    host_name="localhost",
    port=9411,
    # endpoint="api/v2/spans",
    protocol="http",
    # ipv4="",
    # ipv6="",
    # retry=False,
)

exporter = ZipkinSpanExporter(
    service_name="py-service",
    host_name="signalfx-otel-workshop-collector.glitch.me",
    port=443,
    endpoint="/api/v2/spans",
    protocol="https",
)


provider = TracerProvider()
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)
provider.add_span_processor(BatchExportSpanProcessor(exporter))

# instrument http client
http_requests.enable(provider)

# create and instrument flask server
app = Flask(__name__)
app.wsgi_app = OpenTelemetryMiddleware(app.wsgi_app)


@app.route("/")
def hello():
    with tracer.start_as_current_span("fetch-from-node"):
        response = fetch_from_node()
        return "hello from python\n" + response


def fetch_from_node():
    try:
        r = requests.get('http://localhost:8081/')
    except Exception:
        return "error fetching from node"
    return r.text


if __name__ == "__main__":
    app.run(debug=True, port=8082)
