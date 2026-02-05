"""
Prometheus metrics collection for FastAPI
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CollectorRegistry, CONTENT_TYPE_LATEST
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import time
import structlog

logger = structlog.get_logger()

# Create registry
REGISTRY = CollectorRegistry()

# Define metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code'],
    registry=REGISTRY
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint'],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
    registry=REGISTRY
)

REQUEST_SIZE = Histogram(
    'http_request_size_bytes',
    'HTTP request size in bytes',
    ['method', 'endpoint'],
    registry=REGISTRY
)

RESPONSE_SIZE = Histogram(
    'http_response_size_bytes',
    'HTTP response size in bytes',
    ['method', 'endpoint'],
    registry=REGISTRY
)

LLM_REQUEST_LATENCY = Histogram(
    'llm_request_duration_seconds',
    'LLM request latency in seconds',
    ['model'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0),
    registry=REGISTRY
)

LLM_REQUEST_COUNT = Counter(
    'llm_requests_total',
    'Total LLM requests',
    ['model', 'status'],
    registry=REGISTRY
)

DATABASE_QUERY_LATENCY = Histogram(
    'db_query_duration_seconds',
    'Database query latency in seconds',
    ['operation'],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5),
    registry=REGISTRY
)

ACTIVE_REQUESTS = Gauge(
    'http_requests_in_progress',
    'HTTP requests in progress',
    ['method', 'endpoint'],
    registry=REGISTRY
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting Prometheus metrics"""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip metrics endpoint itself
        if request.url.path == '/metrics':
            return await call_next(request)
        
        method = request.method
        endpoint = request.url.path
        
        # Increment in-progress requests
        ACTIVE_REQUESTS.labels(method=method, endpoint=endpoint).inc()
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            logger.error("Unhandled exception in request", error=str(e), path=endpoint, method=method)
            raise
        finally:
            # Calculate latency
            duration = time.time() - start_time
            
            # Record metrics
            REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)
            REQUEST_COUNT.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
            ACTIVE_REQUESTS.labels(method=method, endpoint=endpoint).dec()
            
            logger.info(
                "prometheus.recorded",
                method=method,
                endpoint=endpoint,
                status_code=status_code,
                duration_ms=int(duration * 1000)
            )
        
        return response


def record_llm_request(model: str, duration: float, success: bool = True):
    """Record LLM request metrics"""
    LLM_REQUEST_LATENCY.labels(model=model).observe(duration)
    status = "success" if success else "error"
    LLM_REQUEST_COUNT.labels(model=model, status=status).inc()


def record_db_query(operation: str, duration: float):
    """Record database query metrics"""
    DATABASE_QUERY_LATENCY.labels(operation=operation).observe(duration)


def get_metrics():
    """Return Prometheus metrics in text format"""
    return generate_latest(REGISTRY).decode('utf-8')
