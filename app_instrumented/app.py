import os
import requests
from flask import Flask, request
from opentelemetry import trace
from opentelemetry import metrics
#from opentelemetry.ext.otcollector.trace_exporter import CollectorSpanExporter
from opentelemetry.ext import http_requests
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchExportSpanProcessor
from opentelemetry.sdk.metrics import Counter, Measure, MeterProvider
from opentelemetry.sdk.metrics.export import ConsoleMetricsExporter 
from opentelemetry.sdk.metrics.export.controller import PushController
from opentelemetry.ext.wsgi import OpenTelemetryMiddleware
from opentelemetry.ext.zipkin import ZipkinSpanExporter


#span_exporter = CollectorSpanExporter(
#    service_name="py-service",
#    endpoint=os.getenv("SPAN_EXPORTER_HOST")
#             + ':'
#             + os.getenv("SPAN_EXPORTER_PORT"),
#)

# setup traces
span_exporter = ZipkinSpanExporter(
    service_name="py-service",
    host_name=os.getenv("SPAN_EXPORTER_HOST"),
    port=int(os.getenv("SPAN_EXPORTER_PORT")),
    endpoint=os.getenv("SPAN_EXPORTER_ENDPOINT"),
    protocol=os.getenv("SPAN_EXPORTER_PROTOCOL"),
)


provider = TracerProvider()
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)
provider.add_span_processor(BatchExportSpanProcessor(span_exporter))

# setup metrics
metrics.set_meter_provider(MeterProvider())
meter = metrics.get_meter(__name__)
exporter = ConsoleMetricsExporter()
controller = PushController(meter, exporter, 5)

requests_counter = meter.create_metric(
    name="requests",
    description="number of requests",
    unit="1",
    value_type=int,
    metric_type=Counter,
    label_keys=("path",),
)

# instrument http client
http_requests.enable(provider)

# create and instrument flask server
app = Flask(__name__)
app.wsgi_app = OpenTelemetryMiddleware(app.wsgi_app)


@app.route("/")
def hello():
    with tracer.start_as_current_span("fetch-from-node"):
        requests_counter.add(1, {"path": request.path})
        response = fetch_from_node()
        return "hello from python<br>" + response


def fetch_from_node():
    try:
        r = requests.get(os.getenv("NODE_ENDPOINT") + '/')
    except Exception:
        return "error fetching from node"
    return r.text
