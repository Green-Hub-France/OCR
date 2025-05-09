"""
Module d'observabilité pour OCR - Green Hub.
- Logging structuré au format JSON
- Exposition de métriques Prometheus sans doublons
- Helpers pour instrumenter les appels
"""
import logging
import threading
import json
from typing import Callable, Any
from prometheus_client import start_http_server, Summary, Counter, REGISTRY, generate_latest, CONTENT_TYPE_LATEST
from fastapi import FastAPI
from fastapi.responses import Response
import uvicorn

# ----------- Logging Structuré -----------
class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            'timestamp': self.formatTime(record, self.datefmt),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        if record.exc_info:
            payload['exc_info'] = self.formatException(record.exc_info)
        return json.dumps(payload)

def configure_logging() -> None:
    """Configure le logger racine pour sortir des logs JSON."""
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)

# ----------- Métriques Prometheus -----------
_COUNTER_NAME = 'ocr_greenhub_requests_total'
_LATENCY_NAME = 'ocr_greenhub_request_latency_seconds'

# Création idempotente des métriques
def _ensure_counter():
    try:
        return REGISTRY._names_to_collectors[_COUNTER_NAME]
    except KeyError:
        return Counter(_COUNTER_NAME, 'Nombre total de requêtes traitées', ['type'], registry=REGISTRY)


def _ensure_summary():
    try:
        return REGISTRY._names_to_collectors[_LATENCY_NAME]
    except KeyError:
        return Summary(_LATENCY_NAME, 'Latence de traitement', ['type'], registry=REGISTRY)

REQUEST_COUNTER = _ensure_counter()
REQUEST_LATENCY = _ensure_summary()

# ----------- Serveur FastAPI -----------
app = FastAPI()

@app.get('/healthz')
async def healthz() -> dict:
    return {'status': 'ok'}

@app.get('/metrics')
async def metrics() -> Response:
    data = generate_latest(REGISTRY)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


def start_health_server(host: str = '0.0.0.0', port: int = 8001) -> None:
    """Démarre le serveur FastAPI en thread détaché pour healthz et metrics."""
    def _run():
        uvicorn.run(app, host=host, port=port, log_level='warning')
    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

# ----------- Helper pour instrumentation -----------

def record_request(request_type: str, func: Callable[..., Any], *args, **kwargs) -> Any:
    """Exécute `func`, mesure la latence et incrémente les métriques."""
    with REQUEST_LATENCY.labels(request_type).time():
        result = func(*args, **kwargs)
    REQUEST_COUNTER.labels(request_type).inc()
    return result
