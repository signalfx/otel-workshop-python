## Python Service

This app listens on port `3000` (443 when accessing from outside glitch) and
exposes a single endpoint at `/` that responds with the string `hello from
python`. For every request it receives, it should call the Node service at
`https://signalfx-otel-workshop-node.glitch.me`.

The following modifications can be made:

* The listen port can be modified by editing `.flaskenv`
* The call destination can be modified by setting  `NODE_REQUEST_ENDPOINT` in `.env`

The `.flaskenv` and `.env` files can be used to allow this workshop to be run
in other environments. For example, to run locally, the following changes could
be made:

* In `.flaskenv` set the listen port to `3001`
* In `.env` set the `NODE_REQUEST_ENDPOINT` to `http://localhost:3002`

To run in Docker, set `NODE_REQUEST_ENDPOINT` to `http://host.docker.internal:3002`

## Running the app

The application is available at
https://glitch.com/edit/#!/signalfx-otel-workshop-python. By default, it runs
an uninstrumented version of the application. From the Glitch site, you
should select the name of the Glitch project (top left) and select `Remix
Project`. You will now have a new Glitch project. The name of the project is
listed in the top left of the window.

To run this workshop locally, you'll need Python 3 and Make to be able to run
the service. Install the prerequisites by running `make install`. Next, run
`make run` and then go to http://localhost:3000 to access the app.

## Instrumenting Python HTTP server and client with OpenTelemetry

Your task is to instrument this application using [OpenTelemetry
Python](https://github.com/open-telemetry/opentelemetry-python). If you get
stuck, check out the `app_instrumented` directory.

### 1. Install the required opentelemetry packages

```bash
venv/bin/pip install opentelemetry-ext-http-requests \
    opentelemetry-ext-otcollector opentelemetry-ext-wsgi \
    opentelemetry-sdk
```

Note: You will also find a Flask extension. This is a new extension that is not
as feature rich as the WSGI extension today. In order to show some of the
attributes (tags) that can be automatically added, we are leveraging the WSGI
extension for this workshop.

### 2. Import packages required for instrumenting our Python app

```diff
import requests
from flask import Flask
+from opentelemetry import trace
+#from opentelemetry.ext.otcollector.trace_exporter import CollectorSpanExporter
+from opentelemetry.ext import http_requests
+from opentelemetry.sdk.trace import TracerProvider
+from opentelemetry.sdk.trace.export import BatchExportSpanProcessor
+from opentelemetry.ext.wsgi import OpenTelemetryMiddleware
+from opentelemetry.ext.zipkin import ZipkinSpanExporter
```

Note: The recommended deployment model for OpenTelemetry is to have
applications export in OpenTelemetry (OTLP) format to the OpenTelemetry
Collector and have the OpenTelemetry Collector send to your back-end(s) of
choice. OTLP uses gRPC and unfortunately it does not appear Glitch supports
gRPC In addition, the OpenTelemetry Python instrumentation only supports
OpenCensus format (this should be updated shortly). As a result, this workshop
emits in Zipkin format.

### 3. Configure the tracer and exporter

```diff
import requests
from flask import Flask
from opentelemetry import trace
#from opentelemetry.ext.otcollector.trace_exporter import CollectorSpanExporter
from opentelemetry.ext import http_requests
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchExportSpanProcessor
from opentelemetry.ext.wsgi import OpenTelemetryMiddleware
from opentelemetry.ext.zipkin import ZipkinSpanExporter


+#span_exporter = CollectorSpanExporter(
+#    service_name="py-service",
+#    endpoint=os.getenv("SPAN_EXPORTER_HOST")
+#             + ':'
+#             + os.getenv("SPAN_EXPORTER_PORT"),
+#)

+span_exporter = ZipkinSpanExporter(
+    service_name="py-service",
+    host_name=os.getenv("SPAN_EXPORTER_HOST"),
+    port=int(os.getenv("SPAN_EXPORTER_PORT")),
+    endpoint=os.getenv("SPAN_EXPORTER_ENDPOINT"),
+    protocol=os.getenv("SPAN_EXPORTER_PROTOCOL"),
+)

+provider = TracerProvider()
+trace.set_tracer_provider(provider)
+tracer = trace.get_tracer(__name__)
+provider.add_span_processor(BatchExportSpanProcessor(span_exporter))

app = Flask(__name__)
```

Note: You will notice multiple environment variables used above. These
variables should be set in a `.env` file in the same directory as `app.py`.

```bash
SPAN_EXPORTER_HOST=signalfx-otel-workshop-collector.glitch.me
SPAN_EXPORTER_PORT=443
SPAN_EXPORTER_ENDPOINT=/api/v2/spans
SPAN_EXPORTER_PROTOCOL=https
```

### 4. Instrument flask and requests packages to automatically generate spans

```diff
provider = TracerProvider()
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)
provider.add_span_processor(BatchExportSpanProcessor(span_exporter))

+# instrument http client
+http_requests.enable(provider)

+# create and instrument flask server
app = Flask(__name__)
+app.wsgi_app = OpenTelemetryMiddleware(app.wsgi_app)


@app.route("/")
def hello():
```

Integrations are great as they generate spans for you automatically!

#### 5. Add a manual span to record an interesting operation.

```diff
@app.route("/")
def hello():
+    with tracer.start_as_current_span("fetch-from-node"):
+        response = fetch_from_node()
+        return "hello from python\n" + response
-     response = fetch_from_node()
-     return "hello from python\n" + response
```

This will make our app generate a second span with the operation name
`fetch-from-node`. The span will be a child of the previous auto-generated
span.

We can run the app again and this time it should emit spans to a locally
running OpenTelemetry Collector.
