## Python Service

This app listens on port `8082` and exposes a single endpoint at `/` that resposds with the string `hello from python`. For every request it receives, it calls the Node service at `http://localhost:8081/` and appends the response from the Python service it's own response.

## Running the app

You'll need Python 3 and Make to be able to run the service. 

Run `make run` and then go to http://localhost:8082 to access the app.

## Instrumenting Python HTTP server and client with OpenTelemetry

### 1. Install the required opentelemetry packages

```bash
venv/bin/pip install opentelemetry-ext-http-requests opentelemetry-ext-otcollector opentelemetry-ext-wsgi opentelemetry-sdk
```

### 2. Import packages required for instrumenting our Python app.

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


+# configure tracer and exporter
+ot_exporter = CollectorSpanExporter(
+    service_name="py-service",
+    endpoint="localhost:55678",
+)

+provider = TracerProvider()
+trace.set_tracer_provider(provider)
+tracer = trace.get_tracer(__name__)
+provider.add_span_processor(BatchExportSpanProcessor(ot_exporter))

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

This will make our app generate a second span with operation name as `fetch-from-node`. The span will be a child of the previous auto-generated span.

We can run the app again and this time it should emit spans to locally running OpenTelemetry collector.