import re
from typing import Literal
from urllib.parse import urljoin

from bs4 import BeautifulSoup as Soup

from py_common import log as log
from py_common.types import ScrapedGallery, PerformerSearchResult, ScrapedPerformer, ScrapedTag, ScrapedStudio
from .base import BaseGalleryScraper


class JVID(BaseGalleryScraper):
    domain = ["jvid.com", "www.jvid.com"]

    def __init__(self):
        super().__init__(base_url="https://www.jvid.com")

    def parse_performer_by_url(self, info: dict[Literal["url"], str]) -> ScrapedPerformer:
        log.warning("JVID does not support performer parse")
        return None

    def parse_performer_by_name(self, info: dict[Literal["name"], str]) -> list[PerformerSearchResult]:
        log.warning("JVID does not support performer search")
        return []

    def parse_gallery_by_url(self, info: dict[Literal["url"], str]) -> ScrapedGallery:
        title, details, date, urls, tags, performers, photographer = "", "", "", [info.get("url")], [], [], ""
        resp = self.fetch("get", url=info.get("url"))
        soup = Soup(resp.text, "html.parser")

        if title_elem := soup.select_one(".headline_people"):
            title = title_elem.text.strip() if title_elem else ""

        if info_elem := soup.select_one("div.product_info"):
            if details_elem := info_elem.select_one("div.product_description p"):
                text_list = details_elem.stripped_strings
                details = "\n".join(text_list).strip()

            if time_elem := info_elem.select_one("div.dateStart"):
                if search_result := re.search(r"(\d{4} / \d{2} / \d{2})", time_elem.text.strip()):
                    date = search_result.group(1).replace(" / ", "-")
            tags_elem = info_elem.select("li.mr-8px")
            tags = [
                ScrapedTag(name=tag.text.strip().removeprefix("#"))
                for tag in tags_elem
                if tag.text.strip()
            ]

        if members_elem := soup.select_one("div.member"):
            performer_count = len(members_elem.select("div.model_part a.model_person"))
            if performer_count == 1:
                performer_elem = members_elem.select_one("div.model_part")
                performers.append(ScrapedPerformer(
                    name=performer_elem.select_one("p.person_name").text.strip(),
                    images=[performer_elem.select_one("img").get("src")]
                    if performer_elem.select_one("img") else None,
                    urls=[
                        urljoin(self.base_url, performer_elem.select_one("a.model_person").get("href"))
                    ] if performer_elem.select_one("a.model_person") else []
                ))
            else:  # Can not get performer name without javascript
                pass
            if producer_elem := members_elem.select_one("div.author_part"):
                photographer = producer_elem.select_one("p").text.strip()

        return ScrapedGallery(
            title=title,
            details=details,
            studio=ScrapedStudio(name="JVID"),
            date=date,
            tags=tags,
            performers=performers,
            urls=[info.get("url")],
            photographer=photographer
        )
