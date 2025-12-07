from abc import ABC, abstractmethod
from typing import Sequence, Literal
from urllib.request import getproxies

import cloudscraper
import requests

from py_common.types import ScrapedPerformer, PerformerSearchResult


class BaseGalleryScraper(ABC):
    domain: Sequence[str]  # list of domains this scraper supports

    def __init__(self, base_url: str, http_client: Literal["requests", "cloudscraper"] = "requests"):
        self.base_url = base_url

        if http_client == "requests":
            self.client: requests.Session | cloudscraper.CloudScraper = requests.Session()
        elif http_client == "cloudscraper":
            self.client: requests.Session | cloudscraper.CloudScraper = cloudscraper.create_scraper()
        else:
            raise ValueError(f"Unsupported instance type: {http_client}")

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @property
    def proxies(self) -> dict:
        return getproxies()

    @abstractmethod
    def parse_performer_by_url(self, info: PerformerSearchResult) -> ScrapedPerformer:
        pass

    @abstractmethod
    async def parse_performer_by_name(self, info: PerformerSearchResult) -> PerformerSearchResult:
        pass
