import os
import requests
import logging

logger = logging.getLogger(__name__)

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
TIMEOUT = 60


def _auth_headers(token: str) -> dict:
    """Build authorization header from JWT token."""
    return {"Authorization": f"Bearer {token}"}


def add_product(url: str, target_price: float, token: str) -> dict:
    try:
        response = requests.post(
            f"{API_BASE_URL}/products",
            json={"url": url, "target_price": target_price},
            headers=_auth_headers(token),
            timeout=TIMEOUT,
        )
        return {"status_code": response.status_code, "data": response.json()}
    except requests.exceptions.ConnectionError:
        return {"status_code": 503, "data": {"detail": "Cannot connect to API."}}
    except Exception as e:
        return {"status_code": 500, "data": {"detail": str(e)}}


def get_all_products(token: str) -> list:
    try:
        response = requests.get(
            f"{API_BASE_URL}/products",
            headers=_auth_headers(token),
            timeout=TIMEOUT,
        )
        return response.json() if response.status_code == 200 else []
    except Exception:
        return []


def get_price_history(product_id: int, token: str, limit: int = 50) -> list:
    try:
        response = requests.get(
            f"{API_BASE_URL}/products/{product_id}/history",
            headers=_auth_headers(token),
            params={"limit": limit},
            timeout=TIMEOUT,
        )
        return response.json() if response.status_code == 200 else []
    except Exception:
        return []


def deactivate_product(product_id: int, token: str) -> dict:
    try:
        response = requests.delete(
            f"{API_BASE_URL}/products/{product_id}",
            headers=_auth_headers(token),
            timeout=TIMEOUT,
        )
        return {"status_code": response.status_code, "data": response.json()}
    except requests.exceptions.ConnectionError:
        return {"status_code": 503, "data": {"detail": "Cannot connect to API."}}
    except Exception as e:
        return {"status_code": 500, "data": {"detail": str(e)}}


def check_api_health() -> bool:
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        return response.status_code == 200
    except Exception:
        return False
    
def update_target_price(
    product_id: int,
    new_target_price: float,
    token: str,
) -> dict:
    try:
        response = requests.patch(
            f"{API_BASE_URL}/products/{product_id}/target",
            json={"target_price": new_target_price},
            headers=_auth_headers(token),
            timeout=TIMEOUT,
        )
        return {"status_code": response.status_code, "data": response.json()}
    except requests.exceptions.ConnectionError:
        return {"status_code": 503, "data": {"detail": "Cannot connect to API."}}
    except Exception as e:
        return {"status_code": 500, "data": {"detail": str(e)}}