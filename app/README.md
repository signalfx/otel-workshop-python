## Python Service

This app listens on port `3000` (443 when accessing from outside glitch) and
exposes a single endpoint at `/` that responds with the string `hello from
python`. For every request it receives, it calls the Node service at
`http://localhost:8081/` and appends the response from the Python service it's
own response.

The following modifications can be made:

* The listen port can be modified by editing `.flaskenv`
* The call host and port can be modified by editing `.env`

This modifications make it possible to run this workshop in other environments.
For example, to run locally in Docker, the following changes could be made:

* In `.flaskenv` set the listen port to `3001`
* In `.env` set the call host to `host.docker.internal`

## Running the app

You'll need Python 3 and Make to be able to run the service.

Install the prerequisites by running `make install`. Next, run `make run` and
then go to http://localhost:3000 to access the app.

## Instrumenting Python HTTP server and client with OpenTelemetry

### 1. Install the required opentelemetry packages

```bash
venv/bin/pip install opentelemetry-ext-http-requests \
    opentelemetry-ext-otcollector opentelemetry-ext-wsgi \
    opentelemetry-sdk
```

### 2. Import packages required for instrumenting our Python app

```diff
import requests
from flask import Flask
+from opentelemetry import trace
+from opentelemetry.ext.otcollector.trace_exporter import CollectorSpanExporter
+from opentelemetry.ext import http_requests
+from opentelemetry.sdk.trace import TracerProvider
+from opentelemetry.sdk.trace.export import BatchExportSpanProcessor
+from opentelemetry.ext.wsgi import OpenTelemetryMiddleware
```

### 3. Configure the tracer and exporter

```diff
import requests
from flask import Flask
from opentelemetry import trace
from opentelemetry.ext.otcollector.trace_exporter import CollectorSpanExporter
from opentelemetry.ext import http_requests
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchExportSpanProcessor
from opentelemetry.ext.wsgi import OpenTelemetryMiddleware


+span_exporter = CollectorSpanExporter(
+    service_name="py-service",
+    endpoint=os.getenv("SPAN_EXPORTER_HOST")
+                       + ':'
+                       + os.getenv("SPAN_EXPORTER_PORT"),
+)

+provider = TracerProvider()
+trace.set_tracer_provider(provider)
+tracer = trace.get_tracer(__name__)
+provider.add_span_processor(BatchExportSpanProcessor(span_exporter))

app = Flask(__name__)
```

### 4. Instrument flask and requests packages to automatically generate spans

```diff
provider = TracerProvider()
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)
provider.add_span_processor(BatchExportSpanProcessor(ot_exporter))

+# instrument http client
+http_requests.enable(provider)

+# create and instrument flask server
app = Flask(__name__)
+app.wsgi_app = OpenTelemetryMiddleware(app.wsgi_app)


@app.route("/")
def hello():
```

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

This will make our app generate a second span with operation name as
`fetch-from-node`. The span will be a child of the previous auto-generated
span.

We can run the app again and this time it should emit spans to a locally running
OpenTelemetry Collector.
