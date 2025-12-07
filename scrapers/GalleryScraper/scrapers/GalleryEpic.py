from .base import BaseGalleryScraper
from schemas import PerformerByURLInput, PerformerByURLOutput
from bs4 import BeautifulSoup


class GalleryEpic(BaseGalleryScraper):
    domain = ["galleryepic.com"]

    def __init__(self):
        super().__init__(base_url="https://galleryepic.com")

    def parse_performer_by_url(self, url_info: PerformerByURLInput) -> PerformerByURLOutput:
        resp = self.client.get(url=url_info.get("url"), proxies=self.proxies)
        if resp.status_code != 200:
            self._logger.error("Failed to retrieve URL")

        soup = BeautifulSoup(resp.content, "html.parser")

        name_elem = soup.select_one("h4.scroll-m-20.text-xl.font-semibold.tracking-tight")
        name = name_elem.text.strip() if name_elem else ""

        avatar_elem = soup.select_one("img[variant=avatar]")
        avatar_url = avatar_elem['src'] if avatar_elem else ""

        urls_elem = soup.select_one("div.flex.items-center.space-x-1.w-0.min-w-full.overflow-x-auto")
        urls = []
        if urls_elem:
            for link_elem in urls_elem.find_all("a"):
                href = link_elem.get('href', '')
                urls.append(href)

        return PerformerByURLOutput(
            name=name,
            urls=urls,
            image=avatar_url
        )
