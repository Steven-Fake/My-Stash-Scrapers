import sys
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from py_common import log
from py_common.types import ScrapedPerformer, PerformerSearchResult
from utils import jaccard_similarity
from .base import BaseGalleryScraper


class GalleryEpic(BaseGalleryScraper):
    domain = ["galleryepic.com"]

    def __init__(self):
        super().__init__(base_url="https://galleryepic.com")

    def parse_performer_by_url(self, info: PerformerSearchResult) -> ScrapedPerformer:
        resp = self.client.get(url=info.get("url"), proxies=self.proxies)
        if resp.status_code != 200:
            log.error("Failed to retrieve URL")
            sys.exit(-1)

        soup = BeautifulSoup(resp.content, "html.parser")

        name_elem = soup.select_one("h4.scroll-m-20.text-xl.font-semibold.tracking-tight")
        name = name_elem.text.strip() if name_elem else ""

        avatar_elem = soup.select_one("img[variant=avatar]")
        avatar_url = avatar_elem['src'] if avatar_elem else ""

        urls_elem = soup.select_one("div.flex.items-center.space-x-1.w-0.min-w-full.overflow-x-auto")
        urls = [info.get("url")]
        if urls_elem:
            for link_elem in urls_elem.find_all("a"):
                href = link_elem.get('href', '')
                urls.append(href)

        return ScrapedPerformer(
            name=name,
            urls=urls,
            image=avatar_url
        )

    async def parse_performer_by_name(self, info: PerformerSearchResult) -> list[PerformerSearchResult]:
        name = info.get("name", "")
        resp = self.client.get(url=f"https://galleryepic.com/zh/cosers/1?coserName={name}", proxies=self.proxies)
        if resp.status_code != 200:
            log.error("Failed to retrieve search results")
            sys.exit(-1)

        soup = BeautifulSoup(resp.content, "html.parser")

        result_elem = soup.select_one("div.grid.grid-cols-2")
        if not result_elem:
            return []

        seen_urls: set[str] = set()
        performers: list[PerformerSearchResult] = []
        for url_elem in result_elem.select("a"):
            url = urljoin(self.base_url, url_elem["href"])
            if url in seen_urls:
                continue
            seen_urls.add(url)
            performers.append(PerformerSearchResult(url=url, name=url_elem.text.strip()))
        performers.sort(key=lambda p: jaccard_similarity(p.get("name", ""), name), reverse=True)

        return performers
