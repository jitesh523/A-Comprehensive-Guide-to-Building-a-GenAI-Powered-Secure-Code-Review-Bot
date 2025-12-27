"""
Performance Monitoring and Metrics

Implements Prometheus metrics and OpenTelemetry instrumentation
for comprehensive observability.
"""
from prometheus_client import Counter, Histogram, Gauge, Info
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
import time
from functools import wraps
from typing import Any, Callable
import logging

logger = logging.getLogger(__name__)

# Prometheus Metrics
scan_requests_total = Counter(
    'scan_requests_total',
    'Total number of scan requests',
    ['language', 'status']
)

scan_duration_seconds = Histogram(
    'scan_duration_seconds',
    'Duration of scan operations',
    ['language', 'scanner']
)

llm_requests_total = Counter(
    'llm_requests_total',
    'Total number of LLM API requests',
    ['provider', 'model', 'status']
)

llm_duration_seconds = Histogram(
    'llm_duration_seconds',
    'Duration of LLM API calls',
    ['provider', 'model']
)

llm_tokens_total = Counter(
    'llm_tokens_total',
    'Total number of LLM tokens used',
    ['provider', 'model', 'type']  # type: input or output
)

llm_cost_usd_total = Counter(
    'llm_cost_usd_total',
    'Total LLM cost in USD',
    ['provider', 'model']
)

cache_hits_total = Counter(
    'cache_hits_total',
    'Total number of cache hits',
    ['cache_type']
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total number of cache misses',
    ['cache_type']
)

findings_total = Counter(
    'findings_total',
    'Total number of security findings',
    ['severity', 'language', 'tool']
)

active_scans = Gauge(
    'active_scans',
    'Number of currently active scans'
)

app_info = Info(
    'app',
    'Application information'
)


class PerformanceMonitor:
    """Performance monitoring and metrics collection"""
    
    def __init__(self):
        self.tracer = trace.get_tracer(__name__)
        self.meter = metrics.get_meter(__name__)
        
        # Set app info
        app_info.info({
            'version': '2.0.0',
            'name': 'Secure Code Review Bot'
        })
    
    def track_scan(self, language: str):
        """Context manager to track scan performance"""
        return ScanTracker(language)
    
    def track_llm_call(self, provider: str, model: str):
        """Context manager to track LLM API call performance"""
        return LLMCallTracker(provider, model)
    
    def record_finding(self, severity: str, language: str, tool: str):
        """Record a security finding"""
        findings_total.labels(
            severity=severity,
            language=language,
            tool=tool
        ).inc()
    
    def record_cache_hit(self, cache_type: str = "llm"):
        """Record a cache hit"""
        cache_hits_total.labels(cache_type=cache_type).inc()
    
    def record_cache_miss(self, cache_type: str = "llm"):
        """Record a cache miss"""
        cache_misses_total.labels(cache_type=cache_type).inc()


class ScanTracker:
    """Context manager for tracking scan performance"""
    
    def __init__(self, language: str):
        self.language = language
        self.start_time = None
        self.scanner = "unknown"
    
    def __enter__(self):
        self.start_time = time.time()
        active_scans.inc()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        status = "success" if exc_type is None else "error"
        
        scan_requests_total.labels(
            language=self.language,
            status=status
        ).inc()
        
        scan_duration_seconds.labels(
            language=self.language,
            scanner=self.scanner
        ).observe(duration)
        
        active_scans.dec()
    
    def set_scanner(self, scanner: str):
        """Set the scanner name"""
        self.scanner = scanner


class LLMCallTracker:
    """Context manager for tracking LLM API call performance"""
    
    def __init__(self, provider: str, model: str):
        self.provider = provider
        self.model = model
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        status = "success" if exc_type is None else "error"
        
        llm_requests_total.labels(
            provider=self.provider,
            model=self.model,
            status=status
        ).inc()
        
        llm_duration_seconds.labels(
            provider=self.provider,
            model=self.model
        ).observe(duration)
    
    def record_tokens(self, input_tokens: int, output_tokens: int):
        """Record token usage"""
        llm_tokens_total.labels(
            provider=self.provider,
            model=self.model,
            type="input"
        ).inc(input_tokens)
        
        llm_tokens_total.labels(
            provider=self.provider,
            model=self.model,
            type="output"
        ).inc(output_tokens)
    
    def record_cost(self, cost_usd: float):
        """Record API cost"""
        llm_cost_usd_total.labels(
            provider=self.provider,
            model=self.model
        ).inc(cost_usd)


def setup_instrumentation(app: Any):
    """
    Setup OpenTelemetry instrumentation for FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    # Setup resource
    resource = Resource.create({
        "service.name": "secure-code-review-bot",
        "service.version": "2.0.0"
    })
    
    # Setup tracing
    trace.set_tracer_provider(TracerProvider(resource=resource))
    
    # Setup metrics with Prometheus exporter
    reader = PrometheusMetricReader()
    metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[reader]))
    
    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)
    
    # Instrument Redis
    RedisInstrumentor().instrument()
    
    # Instrument SQLAlchemy
    SQLAlchemyInstrumentor().instrument()
    
    logger.info("OpenTelemetry instrumentation setup complete")


def trace_function(name: str | None = None):
    """
    Decorator to add tracing to a function.
    
    Args:
        name: Optional span name (defaults to function name)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = trace.get_tracer(__name__)
            span_name = name or func.__name__
            
            with tracer.start_as_current_span(span_name):
                return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = trace.get_tracer(__name__)
            span_name = name or func.__name__
            
            with tracer.start_as_current_span(span_name):
                return func(*args, **kwargs)
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Global performance monitor instance
performance_monitor = PerformanceMonitor()
