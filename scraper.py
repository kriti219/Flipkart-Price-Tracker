from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re


def get_rendered_html(url: str) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ))
        page.goto(url, timeout=20000, wait_until="networkidle")
        html = page.content()
        browser.close()
    return html


def clean_title(raw_title: str) -> str:
    if not raw_title:
        return None
    return raw_title.split(" - Buy")[0].strip()


def clean_price(price_raw: str) -> float:
    if not price_raw:
        return None
    digits = re.sub(r"[^\d]", "", price_raw)
    return float(digits) if digits else None


def scrape_flipkart_product(url: str) -> dict:
    html = get_rendered_html(url)
    soup = BeautifulSoup(html, "lxml")

    price_tag = soup.select_one("div.v1zwn21l.v1zwn20._1psv1zeb9._1psv1ze0")
    raw_title = soup.title.get_text(strip=True) if soup.title else None
    price_raw = price_tag.get_text(strip=True) if price_tag else None

    title = clean_title(raw_title)
    price = clean_price(price_raw)

    return {
        "url": url,
        "title": title,
        "price": price,
        "price_raw": price_raw,
    }


if __name__ == "__main__":
    test_url = "https://www.flipkart.com/prestige-1600-w-induction-cooktop-push-button/p/itmfd5167ac9e920?pid=ICTGHH6HQYJUZPA7&lid=LSTICTGHH6HQYJUZPA7BSYO68&marketplace=FLIPKART&q=electronics&store=search.flipkart.com&spotlightTagId=default_BestsellerId_j9e&srno=s_1_21&otracker=search&otracker1=search&fm=Search&iid=33c7f4f9-5b7b-4806-930f-a7e378e664c5.ICTGHH6HQYJUZPA7.SEARCH&ppt=sp&ppn=sp&ssid=nuon3o3vsw0000001782832543993&qH=9ca91fd2ee5f4b46&ov_redirect=true&ov_redirect=true"
    print(scrape_flipkart_product(test_url))