import re
import sys
from datetime import datetime
from typing import Literal
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from py_common import log
from py_common.types import ScrapedPerformer, PerformerSearchResult, ScrapedGallery, ScrapedTag, ScrapedStudio
from utils import jaccard_similarity
from .base import BaseGalleryScraper


class XChina(BaseGalleryScraper):
    domain = ["xchina.co"]

    def __init__(self):
        super().__init__(base_url="https://xchina.co", http_client="cloudscraper")

    def parse_performer_by_url(self, info: dict[Literal["url"], str]) -> ScrapedPerformer:
        resp = self.fetch("get", url=info.get("url"), headers={'accept-language': 'zh-CN,zh;q=0.9'})
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
        if any(["华人" in t for t in tags]):
            country = "CN"
        elif any(["韩国" in t for t in tags]):
            country = "KR"
        else:
            country = None

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

    async def parse_performer_by_name(self, info: dict[Literal["name"], str]) -> list[PerformerSearchResult]:
        name = info.get("name")
        resp = self.fetch(
            "get",
            url=f"https://xchina.co/models/keyword-{name}.html",
            headers={'accept-language': 'zh-CN,zh;q=0.9'}
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

    def parse_gallery_by_url(self, info: dict[Literal["url"], str]) -> ScrapedGallery:
        resp = self.fetch("get", url=info.get("url"), headers={'accept-language': 'zh-CN,zh;q=0.9'})
        soup = BeautifulSoup(resp.content, "html.parser")

        title_elem = soup.select_one("h1.hero-title-item")
        title = title_elem.text.strip() if title_elem else ""

        info_elem = soup.select_one("div.tab-contents")
        if info_elem:
            # tags
            tags: list[ScrapedTag] = [
                ScrapedTag(name=tag_elem.text.strip())
                for tag_elem in info_elem.select("div.tag")
                if tag_elem.text.strip()
            ]
            # studio
            studios_elem = info_elem.select('a[href^="/photos/series"]')
            if len(studios_elem) >= 2:
                studio_elem = studios_elem[1]
                studio = ScrapedStudio(
                    name=studio_elem.text.strip(),
                    url=urljoin(self.base_url, studio_elem["href"])
                )
            else:
                studio = None
            # performers
            performers_elem = info_elem.select("div.model-item")
            performers = [
                self.parse_performer_by_url(info={"url": urljoin(self.base_url, p_elem.parent["href"])})
                for p_elem in performers_elem
            ]
        else:
            tags = []
            studio = None
            performers = []

        return ScrapedGallery(
            title=title,
            urls=[info.get("url")],
            tags=tags,
            studio=studio,
            performers=performers,
        )
