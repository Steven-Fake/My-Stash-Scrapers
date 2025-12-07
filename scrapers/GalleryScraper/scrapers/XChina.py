import re
import sys
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from py_common import log
from py_common.types import ScrapedPerformer, PerformerSearchResult
from utils import jaccard_similarity
from .base import BaseGalleryScraper


class XChina(BaseGalleryScraper):
    domain = ["xchina.co"]

    def __init__(self):
        super().__init__(base_url="https://xchina.co", http_client="cloudscraper")

    def parse_performer_by_url(self, info: PerformerSearchResult) -> ScrapedPerformer:
        resp = self.client.get(
            url=info.get("url"),
            headers={'accept-language': 'zh-CN,zh;q=0.9'},
            proxies=self.proxies
        )
        if resp.status_code != 200:
            log.error("Failed to retrieve URL")
            sys.exit(-1)

        soup = BeautifulSoup(resp.content, "html.parser")

        info_elem = soup.select_one("div.content-box.object-card")
        if not info_elem:
            log.error("No performer info found")
            sys.exit(-1)

        name_container_elem = info_elem.select_one("div.title")
        name = name_container_elem.next.text.strip() if name_container_elem and name_container_elem.next else ""
        aliases = [
            alias_elem.text.strip()
            for alias_elem in (name_container_elem.select("span") or [])
            if alias_elem.text.strip()
        ]

        image_elem = info_elem.select_one("div.object-avatar img")
        image_url = image_elem['src'] if image_elem else None

        tags = [
            tag_elem.text.strip()
            for tag_elem in (info_elem.select("div.tag") or [])
            if tag_elem.text.strip() and not tag_elem.text.strip().isdigit()
        ]

        country = "CN" if any(["华人" in t for t in tags]) else None

        urls_elem = info_elem.select_one("div.links")
        urls = [link_elem['href'] for link_elem in urls_elem.select("a")] if urls_elem else []
        urls.insert(0, info.get("url"))

        details_elem = info_elem.select_one("div.description")
        details = details_elem.text.strip() if details_elem else ""

        if details:
            # try to extract birthdate in YYYY-MM-DD or YYYY年MM月DD日 format
            if match := re.search(r"\d{4}-\d{2}-\d{2}", details):
                birthdate = match.group(0)
            elif match := re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", details):
                year, month, day = match.groups()
                birthdate = datetime(int(year), int(month), int(day)).strftime("%Y-%m-%d")
            else:
                birthdate = None

            # try to find country info
            if "中国" in details or "大陆" in details:
                country = "CN"
            elif "台湾" in details:
                country = "TW"
        else:
            birthdate = None

        return ScrapedPerformer(
            name=name,
            aliases=", ".join(aliases),
            birthdate=birthdate,
            country=country,
            urls=urls,
            details=details,
            image=image_url,
            tags=[{"name": t} for t in tags],
        )

    async def parse_performer_by_name(self, info: PerformerSearchResult) -> list[PerformerSearchResult]:
        name = info.get("name", "")
        resp = self.client.get(
            url=f"https://xchina.co/models/keyword-{name}.html",
            headers={'accept-language': 'zh-CN,zh;q=0.9'},
            proxies=self.proxies
        )
        if resp.status_code != 200:
            log.error("Failed to retrieve search results")
            sys.exit(-1)

        soup = BeautifulSoup(resp.content, "html.parser")

        result_elem = soup.select_one("div.list.model-list")
        if not result_elem:
            return []

        seen_urls: set[str] = set()
        performers: list[PerformerSearchResult] = []
        for url_elem in result_elem.select("div.title a"):
            url = urljoin(self.base_url, url_elem["href"])
            if url in seen_urls:
                continue
            seen_urls.add(url)
            performers.append(PerformerSearchResult(url=url, name=url_elem.text.strip()))
        performers.sort(key=lambda p: jaccard_similarity(p.get("name", ""), name), reverse=True)

        return performers
