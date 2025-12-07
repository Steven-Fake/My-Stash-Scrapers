import re
from typing import Optional

from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag

from schemas import PerformerByURLInput, PerformerByURLOutput
from .base import BaseGalleryScraper


class V2PH(BaseGalleryScraper):
    domain = ["v2ph.com"]

    def __init__(self):
        super().__init__(base_url="https://v2ph.com", http_client="cloudscraper")

    def parse_performer_by_url(self, url_info: PerformerByURLInput) -> PerformerByURLOutput:
        resp = self.client.get(
            url=url_info.get("url"),
            headers={'accept-language': 'zh-CN,zh;q=0.9'},
            proxies=self.proxies
        )
        if resp.status_code != 200:
            self._logger.error("Failed to retrieve URL")

        soup = BeautifulSoup(resp.content, "html.parser")

        info_elem = soup.select_one("div.row.card-body")
        if not info_elem:
            self._logger.error("No performer info found")

        name_elem = info_elem.select_one("h1")
        raw_name = name_elem.text.strip() if name_elem else ""
        if "、" in raw_name:
            aliases = [n.strip() for n in raw_name.split("、")]
            name = aliases.pop(0)
        else:
            name, aliases = raw_name, []

        image_elem = info_elem.select_one("img")
        image_url: Optional[str] = image_elem['src'] if image_elem else None

        keys = [elem.text.strip() for elem in info_elem.select("dt")]
        values = [elem.text.strip() for elem in info_elem.select("dd")]
        info_map = dict(zip(keys, values))
        birthdate = info_map["生日"] if info_map.get("生日") else None
        height = info_map["身高"].strip() if info_map.get("身高") and info_map["身高"].strip().isdigit() else None
        measurements = re.sub(r"\s+", "", info_map["三围"]) if info_map.get("三围") else None

        urls = [link_elem['href'] for link_elem in info_elem.find_all("a")]

        last_child_elem = [i for i in info_elem.contents if isinstance(i, Tag)][-1]
        for string_elem in reversed(last_child_elem.contents):
            if isinstance(string_elem, NavigableString) and string_elem.strip():
                last_text = string_elem.strip()
                break
        else:
            last_text = ""

        return PerformerByURLOutput(
            name=name,
            aliases=",".join(aliases),
            image=image_url,
            birthdate=birthdate,
            height=height,
            measurements=measurements,
            urls=urls,
            details=last_text
        )
