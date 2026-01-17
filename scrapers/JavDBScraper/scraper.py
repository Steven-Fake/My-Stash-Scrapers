import re
from typing import Optional
from urllib.parse import urljoin
from urllib.request import getproxies

import unicodedata
from bs4 import BeautifulSoup
from cloudscraper import create_scraper, CloudScraper

from py_common.types import ScrapedPerformer, ScrapedScene, ScrapedStudio, ScrapedTag, SceneSearchResult, \
    PerformerSearchResult


class JavDB:
    base_url = "https://javdb.com"

    def __init__(self):
        self.client: CloudScraper = create_scraper()

    def fetch_soup(self, url: str) -> BeautifulSoup:
        resp = self.client.get(
            url=url, proxies=getproxies(), headers={
                "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            }
        )
        resp.raise_for_status()
        return BeautifulSoup(resp.content, "html.parser")

    def search_scenes(self, keyword: str) -> list[SceneSearchResult]:
        soup = self.fetch_soup(urljoin(self.base_url, f"/search?q={keyword}&f=all"))
        result = []
        for movie_elem in soup.select("div.movie-list div.item"):
            title = movie_elem.select_one("div.video-title").text.strip()
            url = urljoin(self.base_url, movie_elem.select_one("a.box").attrs.get("href"))

            image_elem = movie_elem.select_one("div.cover img")
            image = image_elem.attrs.get("src") if image_elem else None
            date_elem = movie_elem.select_one("div.meta")
            date = (
                date_elem.text.strip()
                if date_elem and re.match(r"\d{4}-\d{2}-\d{2}", date_elem.text.strip())
                else None
            )
            result.append(SceneSearchResult(title=title, url=url, image=image, date=date))
        return result

    def search_scene(self, keyword: str) -> Optional[str]:
        soup = self.fetch_soup(urljoin(self.base_url, f"/search?q={keyword}&f=all"))
        for movie_elem in soup.select("div.movie-list div.item"):
            title = movie_elem.select_one("div.video-title").text.strip()
            if keyword.upper() in title.upper():
                return urljoin(self.base_url, movie_elem.select_one("a.box").attrs.get("href"))
        return None

    def search_performers(self, keyword: str) -> list[PerformerSearchResult]:
        soup = self.fetch_soup(urljoin(self.base_url, f"/search?q={keyword}&f=actor"))
        result = []
        for actor in soup.select("div.box.actor-box"):
            name = actor.select_one("strong").text.strip()
            url = urljoin(self.base_url, actor.select_one("a").attrs.get("href"))
            result.append(PerformerSearchResult(name=name, url=url))
        return result

    def parse_performer(self, url: str) -> ScrapedPerformer:
        soup = self.fetch_soup(url)
        name, aliases, image, urls = None, None, None, [url]

        name_elem = soup.select_one("span.actor-section-name")
        if name_elem:
            all_names = [name.strip() for name in name_elem.text.split(",")]
            name = all_names.pop()
            aliases = ", ".join(all_names) if all_names else None

        avatar_elem = soup.select_one("span.avatar")
        if avatar_elem:
            image_style = avatar_elem.attrs["style"]
            image = re.search(r'url\((.+?)\)', image_style).group(1)

        buttons_container = soup.select_one("div.column.section-addition")
        if buttons_container:
            for link_elem in buttons_container.select("a.button.is-info"):
                link = link_elem.attrs["href"]
                urls.append(link)

        return ScrapedPerformer(
            name=name,
            aliases=aliases,
            urls=urls,
            image=image
        )

    def parse_jav(self, url: str) -> ScrapedScene:
        soup = self.fetch_soup(url)
        # Title
        title_elem = soup.select_one("strong.current-title")
        title = title_elem.text.strip() if title_elem else ""
        # Image
        image_container_elem = soup.select_one("div.column-video-cover")
        if image_container_elem and image_container_elem.select_one("img"):
            image = image_container_elem.select_one("img")["src"]
        else:
            image = None

        # Metadata
        code, date, studio, tags, performers, urls = None, None, None, [], [], [url]
        metadata_container_elem = soup.select_one("nav.panel.movie-panel-info")
        if metadata_container_elem:
            metadata_elems = metadata_container_elem.select("div.panel-block")
            for info in metadata_elems:
                text = unicodedata.normalize("NFKD", re.sub("[\n ]", "", info.text))
                if re.search("番號:.+", text):
                    code = info.select_one("span.value").text.strip()
                elif re.search("日期:.+", text):
                    date = info.select_one("span.value").text.strip() or None
                elif re.search("片商:.+", text):
                    studio_name = info.select_one("span.value").text
                    studio = ScrapedStudio(name=studio_name.strip())
                elif re.search("系列:.+", text):  # TODO
                    pass
                elif re.search("類別:.+", text):
                    tags_container = info.select_one("span.value")
                    for tag in tags_container.select("a"):
                        tags.append(ScrapedTag(name=tag.text.strip()))
                elif re.search("演員:.+", text):
                    actor_container = info.select_one("span.value")
                    actor_elems = actor_container.select("a, strong")
                    for actor, gender in zip(actor_elems[::2], actor_elems[1::2]):
                        if gender.text.strip() != "♀":
                            continue
                        performer_name = actor.text.strip()
                        performer_url = urljoin(self.base_url, actor["href"])
                        performer = self.parse_performer(performer_url)
                        if not performer.get("name"):
                            performer.name = performer_name
                        performers.append(performer)
                elif info.select_one("div.control.ranking-tags"):
                    for tag in info.select("a.tags"):
                        if "JavDB 影片TOP250" in tag.text:
                            tags.append(ScrapedTag(name="JavDB TOP250"))
                        elif "JavDB 有碼影片TOP250" in tag.text:
                            tags.append(ScrapedTag(name="JavDB 有码影片TOP250"))
                        elif "JavDB 無碼影片TOP250" in tag.text:
                            tags.append(ScrapedTag(name="JavDB 无码影片TOP250"))
                        elif "年度TOP250" in tag.text:
                            tags.append(ScrapedTag(name="JavDB 年度TOP250"))

        # URLs
        url_container = soup.select_one("div#magnets-content")
        if url_container:
            for link_elem in url_container.select("button.button.is-small.copy-to-clipboard"):
                magnet_link = link_elem.attrs.get("data-clipboard-text")
                if magnet_link:
                    urls.append(magnet_link)

        return ScrapedScene(
            title=title,
            code=code,
            image=image,
            date=date,
            studio=studio,
            tags=tags,
            performers=performers,
            urls=urls
        )
