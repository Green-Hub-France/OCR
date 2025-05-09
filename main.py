import os
import logging
from src.health import start_health_server
from src.ui import app

logger = logging.getLogger(__name__)

def main():
    disable = os.getenv("DISABLE_HEALTH", "").lower() in ("1","true","yes")
    logger.info(f"[DEBUG] DISABLE_HEALTH = {disable}")
    if not disable:
        # Only launch if it’s not explicitly disabled
        start_health_server(host="0.0.0.0", port=8002)
    else:
        logger.info("Health server disabled by DISABLE_HEALTH")

    # 3. Lancement de l'UI Streamlit
    app()

if __name__ == "__main__":
    main()