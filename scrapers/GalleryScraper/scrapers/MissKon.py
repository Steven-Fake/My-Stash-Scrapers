from typing import Literal
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from py_common import log as log
from py_common.types import ScrapedPerformer, PerformerSearchResult, ScrapedGallery, ScrapedStudio
from .base import BaseGalleryScraper


class MissKon(BaseGalleryScraper):
    domain = ["misskon.com"]

    def __init__(self):
        super().__init__(base_url="https://misskon.com")

    def parse_performer_by_url(self, info: dict[Literal["url"], str]) -> ScrapedPerformer:
        """
        The MissKon site uses tags to record performer information. The URLs users receive do not contain the tag ID, therefore I have restricted `performerByURL` in the metadata.
        :param info:
        :return:
        """
        resp = self.fetch("get", url=info.get("url"))
        data: dict = resp.json()

        return ScrapedPerformer(
            name=data.get("name", ""),
            urls=[data.get("link", "")]
        )

    def parse_performer_by_name(self, info: dict[Literal["name"], str]) -> list[PerformerSearchResult]:
        """
        The MissKon site does not have performer pages, so this is a stub implementation.
        :param info:
        :return:
        """
        log.warning("MissKon does not support performer search")
        return []

    def parse_gallery_by_url(self, info: dict[Literal["url"], str]) -> ScrapedGallery:
        url_path = urlparse(info.get("url")).path
        post_id = url_path[1:].split("-")[0]
        api_url = urljoin(self.base_url, f"/wp-json/wp/v2/posts/{post_id}")
        resp = self.fetch("get", url=api_url)
        data: dict = resp.json()

        urls = [info.get("url"), api_url]

        performers: list[ScrapedPerformer] = [
            self.parse_performer_by_url({
                "url": urljoin(self.base_url, f"/wp-json/wp/v2/tags/{performer_id}")
            })
            for performer_id in data.get("tags", [])
        ]

        content = data.get("content", {}).get("rendered", "")  # HTML
        soup = BeautifulSoup(content, "html.parser")
        url_elems = soup.select("a.shortc-button")
        if url_elems:
            urls.extend([url_elem["href"] for url_elem in url_elems if url_elem.get("href")])

        return ScrapedGallery(
            title=data.get("title", {}).get("rendered", ""),
            urls=urls,
            performers=performers
        )
