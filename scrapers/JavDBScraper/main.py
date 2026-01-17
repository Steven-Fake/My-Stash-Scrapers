import json
import sys
from typing import Literal, Optional

from py_common import log
from py_common.deps import ensure_requirements
from py_common.types import ScrapedScene, SceneSearchResult, PerformerSearchResult, ScrapedPerformer
from .scraper import JavDB

ensure_requirements("bs4:beautifulsoup4", "requests", "cloudscraper")


def scene_by_url(url_info: dict[Literal["url"], str]) -> ScrapedScene:
    if not url_info.get("url"):
        log.error("No URL provided")
        sys.exit(-1)
    return JavDB().parse_jav(url_info.get("url"))


def scene_by_name(title_info: dict[Literal["title"], str]) -> list[SceneSearchResult]:
    if not title_info.get("title"):
        log.error("No Title provided")
        sys.exit(-1)
    return JavDB().search_scenes(title_info.get("title"))


def scene_by_fragment(fragment_info: dict) -> Optional[ScrapedScene]:
    if not fragment_info.get("title") and not fragment_info.get("code"):
        log.error("No Title or Code provided")
        sys.exit(-1)
    scraper = JavDB()
    target_url = scraper.search_scene(fragment_info.get("code") or fragment_info.get("title"))
    if not target_url:
        return None
    else:
        return scraper.parse_jav(target_url)


def performer_by_name(name_info: dict[Literal["name"], str]) -> list[PerformerSearchResult]:
    if not name_info.get("name"):
        log.error("No Title provided")
        sys.exit(-1)
    return JavDB().search_performers(name_info.get("name"))


def performer_by_url(url_info: dict[Literal["url"], str]) -> ScrapedPerformer:
    if not url_info.get("url"):
        log.error("No URL provided")
        sys.exit(-1)
    return JavDB().parse_performer(url_info.get("url"))


if __name__ == "__main__":
    info = json.loads(sys.stdin.read())

    if sys.argv[1] == "sceneByURL":
        print(json.dumps(scene_by_url(info), ensure_ascii=False))
    elif sys.argv[1] == "sceneByName":
        print(json.dumps(scene_by_name(info), ensure_ascii=False))
    elif sys.argv[1] == "sceneByFragment":
        print(json.dumps(scene_by_fragment(info), ensure_ascii=False))
    elif sys.argv[1] == "performerByURL":
        print(json.dumps(performer_by_url(info), ensure_ascii=False))
    elif sys.argv[1] == "performerByName":
        print(json.dumps(performer_by_name(info), ensure_ascii=False))
