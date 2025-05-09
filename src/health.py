# src/health.py
# --------------------
"""
Health check and Prometheus metrics endpoint for OCR - Green Hub.
Exposes /healthz and /metrics using FastAPI.
"""
import threading
import uvicorn
from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, REGISTRY

app = FastAPI()

@app.get("/healthz")
async def healthz():
    """Health check endpoint."""
    return {"status": "ok"}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    data = generate_latest(REGISTRY)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


def start_health_server(host: str = "0.0.0.0", port: int = 8001) -> None:
    """
    Démarre le serveur FastAPI en thread détaché pour healthz et metrics.
    """
    def _run():
        uvicorn.run(app, host=host, port=port, log_level="warning")
    thread = threading.Thread(target=_run, daemon=True)
    thread.start()