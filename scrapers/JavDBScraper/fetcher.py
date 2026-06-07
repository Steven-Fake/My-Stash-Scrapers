from typing import Literal
from urllib.request import getproxies

from requests import post

JINA_API_KEY = ""
JINA_ENDPOINT = "https://r.jina.ai"

FIRECRAWL_API_KEY = ""
FIRECRAWL_ENDPOINT = "https://api.firecrawl.dev/v2/scrape"


def fetch_html(url: str, source: Literal["JINA", "FIRECRAWL"]) -> str:
    if source == "JINA":
        return _jina_fetch_html(url)
    elif source == "FIRECRAWL":
        return _firecrawl_fetch_html(url)
    else:
        raise ValueError(f"Unknown web reader: {source}")


def _get_proxies() -> dict[str, str]:
    proxies = getproxies()
    if 'http' in proxies and 'https' not in proxies:
        proxies['https'] = proxies['http']
    return proxies


def _jina_fetch_html(url: str) -> str:
    headers = {
        "Content-Type": "application/json",
        "DNT": "1",
        "X-Locale": "zh-CN",
        "X-Retain-Images": "none",
        "X-Return-Format": "html"
    }
    if JINA_API_KEY:
        headers["Authorization"] = f"Bearer {JINA_API_KEY}"

    resp = post(
        url=JINA_ENDPOINT,
        proxies=_get_proxies(),
        headers=headers,
        json={"url": url},
    )
    resp.raise_for_status()
    return resp.text


def _firecrawl_fetch_html(url: str) -> str:
    headers = {"Content-Type": "application/json"}
    if FIRECRAWL_API_KEY:
        headers["Authorization"] = f"Bearer {FIRECRAWL_API_KEY}"

    resp = post(
        url=FIRECRAWL_ENDPOINT,
        proxies=_get_proxies(),
        headers=headers,
        json={
            "url": url,
            "formats": ["html"],
            "onlyMainContent": True,
            "headers": {"accept-language": "zh-CN,zh;q=0.9"},
            "location": {"country": "US", "languages": ["zh-CN"]},
        }
    )
    resp.raise_for_status()
    return resp.text
