from typing import Literal
from urllib.parse import urlsplit, urljoin

from bs4 import BeautifulSoup, Tag

from py_common import log as log
from py_common.types import ScrapedPerformer, PerformerSearchResult, ScrapedGallery, ScrapedTag
from .base import BaseGalleryScraper


class EHentai(BaseGalleryScraper):
    domain = ["e-hentai.org"]

    def __init__(self):
        super().__init__(base_url="https://e-hentai.org")

    def parse_performer_by_url(self, info: dict[Literal["url"], str]) -> ScrapedPerformer:
        """
        The EHentai site does not have performer pages, so this is a stub implementation.
        :param info:
        :return:
        """
        log.warning("EHentai does not support performer search")
        return ScrapedPerformer(
            name=""
        )

    def parse_performer_by_name(self, info: dict[Literal["name"], str]) -> list[PerformerSearchResult]:
        """
        The EHentai site does not have performer pages, so this is a stub implementation.
        :param info:
        :return:
        """
        log.warning("EHentai does not support performer search")
        return []

    def parse_gallery_by_url(self, info: dict[Literal["url"], str]) -> ScrapedGallery:
        resp = self.fetch("get", url=info.get("url"), headers={'accept-language': 'zh-CN,zh;q=0.9'})
        soup = BeautifulSoup(resp.content, "html.parser")

        title_elem = soup.select_one("h1#gn")
        title = title_elem.text.strip() if title_elem else ""

        tags: list[ScrapedTag] = []
        performers: list[ScrapedPerformer] = []
        urls: list[str] = [info.get("url")]

        info_elem = soup.select_one("div#taglist")
        if info_elem:
            info_map: dict[str, list[Tag]] = {
                tag_elem.select_one("td.tc").text.strip(): list(tag_elem.select("a"))
                for tag_elem in info_elem.select("tr")
            }
            for k in info_map.keys():
                if k in ("parody:", "character:", "female:", "other:"):
                    tags.extend([ScrapedTag(name=tag.text.strip()) for tag in info_map[k]])
                elif k in ("cosplayer:", "artist:"):
                    performers.extend([
                        ScrapedPerformer(
                            name=tag.text.strip(),
                            urls=[tag["href"]]
                        ) for tag in info_map[k]
                    ])
        # parse download urls
        base_path = urlsplit(info.get("url")).path
        [gid, t] = base_path.replace("/g/", "").split("/")[:2]
        download_page = urljoin(self.base_url, "gallerytorrents.php?gid={}&t={}".format(gid, t))
        download_resp = self.fetch("get", url=download_page, headers={'accept-language': 'zh-CN,zh;q=0.9'})
        download_soup = BeautifulSoup(download_resp.content, "html.parser")
        download_form_elem = download_soup.select_one("form")
        if download_form_elem:
            for elem in download_form_elem.select("a"):
                urls.append(elem["href"])

        return ScrapedGallery(
            title=title,
            tags=tags,
            urls=urls,
            performers=performers
        )
