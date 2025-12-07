import re
import sys
from typing import Literal
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag

from py_common import log
from py_common.types import ScrapedPerformer, PerformerSearchResult, ScrapedGallery, ScrapedStudio
from utils import jaccard_similarity
from .base import BaseGalleryScraper


class V2PH(BaseGalleryScraper):
    domain = ["v2ph.com"]

    def __init__(self):
        super().__init__(base_url="https://v2ph.com", http_client="cloudscraper")

    def parse_performer_by_url(self, info: dict[Literal["url"], str]) -> ScrapedPerformer:
        resp = self.fetch("get", url=info.get("url"), headers={'accept-language': 'zh-CN,zh;q=0.9'})
        soup = BeautifulSoup(resp.content, "html.parser")

        info_elem = soup.select_one("div.row.card-body")
        if not info_elem:
            log.error("No performer info found")
            sys.exit(-1)

        name_elem = info_elem.select_one("h1")
        raw_name = name_elem.text.strip() if name_elem else ""
        if "、" in raw_name:
            aliases = [n.strip() for n in raw_name.split("、")]
            name = aliases.pop(0)
        else:
            name, aliases = raw_name, []

        image_elem = info_elem.select_one("img")
        image_url = image_elem['src'] if image_elem else None

        keys = [elem.text.strip() for elem in info_elem.select("dt")]
        values = [elem.text.strip() for elem in info_elem.select("dd")]
        info_map = dict(zip(keys, values))
        birthdate = info_map["生日"] if info_map.get("生日") else None
        height = info_map["身高"].strip() if info_map.get("身高") and info_map["身高"].strip().isdigit() else None
        measurements = re.sub(r"\s+", "", info_map["三围"]) if info_map.get("三围") else None

        urls = [link_elem['href'] for link_elem in info_elem.find_all("a")]
        urls.insert(0, info.get("url"))

        last_child_elem = [i for i in info_elem.contents if isinstance(i, Tag)][-1]
        for string_elem in reversed(last_child_elem.contents):
            if isinstance(string_elem, NavigableString) and string_elem.strip():
                last_text = string_elem.strip()
                break
        else:
            last_text = ""

        return ScrapedPerformer(
            name=name,
            aliases=", ".join(aliases),
            image=image_url,
            birthdate=birthdate,
            height=height,
            measurements=measurements,
            urls=urls,
            details=last_text
        )

    async def parse_performer_by_name(self, info: dict[Literal["name"], str]) -> list[PerformerSearchResult]:
        name = info.get("name")
        resp = self.fetch(
            "get",
            url=f"https://www.v2ph.com/search/?q={name}",
            headers={'accept-language': 'zh-CN,zh;q=0.9'},
        )
        soup = BeautifulSoup(resp.content, "html.parser")

        result_elem = soup.select_one("div.container.main-wrap")
        if not result_elem:
            return []

        seen_urls: set[str] = set()
        performers: list[PerformerSearchResult] = []
        for url_elem in result_elem.select('a[href^="/actor"]'):
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

        info_elem = soup.select_one("div.container.main-wrap > div.card")
        if not info_elem:
            log.error("No gallery info found")
            sys.exit(-1)

        title_elem = info_elem.select_one("h1.h5.text-center")
        title = title_elem.text.strip() if title_elem else ""

        keys = [elem.text.strip() for elem in info_elem.select("dt")]
        values = [elem for elem in info_elem.select("dd")]
        info_map: dict[str, Tag] = dict(zip(keys, values))

        studio = ScrapedStudio(
            name=info_map["拍摄机构"].text.strip(),
            url=urljoin(self.base_url, info_map["拍摄机构"].find("a")['href'])
        ) if info_map.get("拍摄机构") else None
        performers: list[ScrapedPerformer] = [
            self.parse_performer_by_url({"url": urljoin(self.base_url, link_elem['href'])})
            for link_elem in info_map["出镜模特"].find_all("a")
        ] if info_map.get("出镜模特") else []
        date = info_map["发行日期"].text.strip() if info_map.get("发布日期") else None
        code = info_map["专辑编号"].text.strip() if info_map.get("专辑编号") else None
        tags = [
            {"name": tag_elem.text.strip()}
            for tag_elem in info_map["专辑标签"].find_all("a")
        ] if info_map.get("专辑标签") else []

        return ScrapedGallery(
            title=title,
            urls=[info.get("url")],
            studio=studio,
            performers=performers,
            date=date,
            code=code,
            tags=tags
        )
