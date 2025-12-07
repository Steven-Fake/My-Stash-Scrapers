from typing import Literal
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from py_common.types import ScrapedPerformer, PerformerSearchResult, ScrapedGallery
from utils import jaccard_similarity
from .base import BaseGalleryScraper


class GalleryEpic(BaseGalleryScraper):
    domain = ["galleryepic.com"]

    def __init__(self):
        super().__init__(base_url="https://galleryepic.com")

    def parse_performer_by_url(self, info: dict[Literal["url"], str]) -> ScrapedPerformer:
        resp = self.fetch("get", url=info.get("url"))
        soup = BeautifulSoup(resp.content, "html.parser")

        name_elem = soup.select_one("h4.scroll-m-20.text-xl.font-semibold.tracking-tight")
        name = name_elem.text.strip() if name_elem else None

        image_elem = soup.select_one("img[variant=avatar]")
        image_url = image_elem['src'] if image_elem else None

        urls_elem = soup.select_one("div.flex.items-center.space-x-1.w-0.min-w-full.overflow-x-auto")
        urls = [info.get("url")]
        if urls_elem:
            for link_elem in urls_elem.find_all("a"):
                href = link_elem.get('href', '')
                urls.append(href)

        return ScrapedPerformer(
            name=name,
            urls=urls,
            image=image_url
        )

    async def parse_performer_by_name(self, info: dict[Literal["name"], str]) -> list[PerformerSearchResult]:
        name = info.get("name")
        resp = self.fetch("get", url=f"https://galleryepic.com/zh/cosers/1?coserName={name}")
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

    def parse_gallery_by_url(self, info: dict[Literal["url"], str]) -> ScrapedGallery:
        resp = self.fetch("get", url=info.get("url"))
        soup = BeautifulSoup(resp.content, "html.parser")

        info_elem = soup.select_one("div.w-full div.flex.justify-between.items-center")
        if info_elem:
            info_elem = info_elem.parent
            title_elem = info_elem.select_one("h2")
            title = title_elem.text.strip() if title_elem else ""
        else:
            title = None

        breadcrumb_elem = soup.select_one("div.w-full > div.py-3")
        if breadcrumb_elem:
            performers: list[ScrapedPerformer] = []
            for link_elem in breadcrumb_elem.select('a[href^="/zh/coser/"]'):
                url = urljoin(self.base_url, link_elem['href'])
                name = link_elem.text.strip()
                if "album" in info.get("url"):
                    url = url.replace("/coser/", "/model/")  # Fix the wrong performer URL in album pages
                performer = self.parse_performer_by_url({"url": url})
                if not performer.get("name"):
                    performer["name"] = name
                performers.append(performer)
        else:
            performers = []

        return ScrapedGallery(
            title=title,
            urls=[info.get("url")],
            performers=performers
        )
