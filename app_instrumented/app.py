import os
import requests
from flask import Flask
from opentelemetry import trace
from opentelemetry import propagators
#from opentelemetry.ext.otcollector.trace_exporter import CollectorSpanExporter
from opentelemetry.ext import http_requests
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchExportSpanProcessor
from opentelemetry.ext.wsgi import OpenTelemetryMiddleware
from opentelemetry.ext.zipkin import ZipkinSpanExporter


#span_exporter = CollectorSpanExporter(
#    service_name="py-service",
#    endpoint=os.getenv("SPAN_EXPORTER_HOST")
#                       + ':'
#                       + os.getenv("SPAN_EXPORTER_PORT"),
#)

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
        r = requests.get('http://'
                         + os.getenv("REQUEST_HOST")
                         + ':'
                         + os.getenv("REQUEST_PORT")
                         + '/')
    except Exception:
        return "error fetching from node"
    return r.text
