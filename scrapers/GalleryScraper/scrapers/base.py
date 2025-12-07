from abc import ABC, abstractmethod
from typing import Sequence, Literal
import requests
import cloudscraper
from urllib.request import getproxies
import sys

from schemas import PerformerByURLInput, PerformerByURLOutput


class Logger:

    def __init__(self, name: str):
        self.name = name

    @property
    def logger_name(self) -> str:
        return self.name

    def error(self, message: str):
        sys.stderr.write(f"[{self.logger_name}] ERROR: {message}\n")
        sys.exit(-1)

    def warning(self, message: str):
        sys.stderr.write(f"[{self.logger_name}] WARNING: {message}\n")


class BaseGalleryScraper(ABC):
    domain: Sequence[str]  # list of domains this scraper supports

    def __init__(self, base_url: str, http_client: Literal["requests", "cloudscraper"] = "requests"):
        self.base_url = base_url
        self._logger = Logger(f"{self.__class__.__name__} Scraper")

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
    def parse_performer_by_url(self, url_info: PerformerByURLInput) -> PerformerByURLOutput:
        pass
