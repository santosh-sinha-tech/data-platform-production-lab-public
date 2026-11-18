import json
import threading
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter, SpanExportResult
from prometheus_client import CollectorRegistry, Counter, Histogram

class LocalExporter(SpanExporter):
    """Allowlist-only single-process exporter; optional local JSONL file."""
    def __init__(self, path: str | None=None):
        self.path=path
        self.spans=[]
        self.lock=threading.Lock()
    def export(self, spans):
        with self.lock:
            for s in spans:
                row=dict(name=s.name,trace_id=f'{s.context.trace_id:032x}',span_id=f'{s.context.span_id:016x}',
                         parent_id=f'{s.parent.span_id:016x}' if s.parent else None,
                         duration_ms=(s.end_time-s.start_time)/1e6,status=s.status.status_code.name,
                         attributes={k:v for k,v in s.attributes.items() if k in {'http.response.status_code','model.profile','attempt','failure.category'}})
                self.spans.append(row)
                if len(self.spans)>10000:
                    del self.spans[:-10000]
                if self.path:
                    with open(self.path,'a') as f:
                        f.write(json.dumps(row)+'\n')
        return SpanExportResult.SUCCESS
    def shutdown(self):
        pass

class Telemetry:
    def __init__(self, trace_path: str | None=None):
        self.exporter=LocalExporter(trace_path)
        self.provider=TracerProvider()
        self.provider.add_span_processor(SimpleSpanProcessor(self.exporter))
        self.tracer=self.provider.get_tracer('ai-observability-lab')
        self.registry=CollectorRegistry()
        self.requests=Counter('ai_requests','Completed requests',['status','failure_category'],registry=self.registry)
        self.attempts=Counter('ai_provider_attempts','All billed simulated attempts',['model_profile','status'],registry=self.registry)
        self.admissions=Counter('ai_admission_attempts','Valid authenticated admission attempts including rejections',registry=self.registry)
        self.rejections=Counter('ai_rate_limit_rejections','Valid admission attempts rejected by fixed-window tenant quota',registry=self.registry)
        self.retries=Counter('ai_retries','Additional primary calls',registry=self.registry)
        self.fallbacks=Counter('ai_fallbacks','Fallback requests',registry=self.registry)
        self.degraded=Counter('ai_quality_failures','Evaluated successful requests failing quality',registry=self.registry)
        self.cost=Counter('ai_simulated_cost_dollars','Simulated billed attempt cost',['model_profile'],registry=self.registry)
        self.duration=Histogram('ai_stage_seconds','Measured durations',['route','stage'],
                                buckets=(.005,.01,.025,.05,.08,.1,.2,.5,1),registry=self.registry)
