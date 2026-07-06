import requests
import os
import logging

logger = logging.getLogger(__name__)

def ping_api():
    """
    Ping the deployed FastAPI health check endpoint.
    Called by GitHub Actions on the same cron schedule as the scraper
    so the API is always warm when the scraper needs it.
    """
    api_url = os.getenv("API_BASE_URL")
    if not api_url:
        logger.info("API_BASE_URL not set, skipping ping")
        return

    try:
        response = requests.get(f"{api_url}/", timeout=10)
        logger.info(f"API ping: {response.status_code}")
    except Exception as e:
        logger.warning(f"API ping failed: {e}")

if __name__ == "__main__":
    ping_api()