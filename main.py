from src.ui import app
from src.observability import configure_logging
from src.health import start_health_server

import os, logging
logger = logging.getLogger(__name__)
logger.info(f"[DEBUG] DISABLE_HEALTH = {os.getenv('DISABLE_HEALTH')}")

if __name__ == '__main__':
    # Configure structured JSON logging
    configure_logging()
    # Start health and metrics HTTP server on port 8001
    start_health_server(host='0.0.0.0', port=8001)
    # Launch Streamlit application
    app()