from bs4 import BeautifulSoup
import re
from schemas import PerformerByURLInput, PerformerByURLOutput
from .base import BaseGalleryScraper


class XChina(BaseGalleryScraper):
    domain = ["xchina.co"]

    def __init__(self):
        super().__init__(base_url="https://xchina.co", http_client="cloudscraper")

    def parse_performer_by_url(self, url_info: PerformerByURLInput) -> PerformerByURLOutput:
        resp = self.client.get(
            url=url_info.get("url"),
            headers={'accept-language': 'zh-CN,zh;q=0.9'},
            proxies=self.proxies
        )
        if resp.status_code != 200:
            self._logger.error("Failed to retrieve URL")

        soup = BeautifulSoup(resp.content, "html.parser")

        info_elem = soup.select_one("div.content-box.object-card")
        if not info_elem:
            self._logger.error("No performer info found")

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

        urls_elem = info_elem.select_one("div.links")
        urls = [link_elem['href'] for link_elem in urls_elem.select("a")] if urls_elem else []

        details_elem = info_elem.select_one("div.description")
        details = details_elem.text.strip() if details_elem else ""

        if details:
            birthdate = re.search(r"\d{4}-\d{2}-\d{2}", details)
            birthdate = birthdate.group(0) if birthdate else None
        else:
            birthdate = None

        return PerformerByURLOutput(
            name=name,
            tags=[{"name": t} for t in tags],
            aliases=", ".join(aliases),
            image=image_url,
            birthdate=birthdate,
            urls=urls,
            details=details
        )
