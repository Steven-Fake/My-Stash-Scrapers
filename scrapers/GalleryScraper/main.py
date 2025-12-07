import json
import sys
from urllib.parse import urlsplit

from schemas import PerformerByURLInput, PerformerByURLOutput
from scrapers import GalleryEpic, V2PH, XChina

all_scrapers = [
    GalleryEpic, V2PH, XChina
]


def performer_by_url(url_info: PerformerByURLInput) -> PerformerByURLOutput:
    if not url_info.get("url"):
        sys.stderr.write("No URL provided\n")
        sys.exit(-1)

    domain = urlsplit(url_info["url"]).netloc.lower()
    for scraper_cls in all_scrapers:
        if domain in scraper_cls.domain:
            scraper = scraper_cls()
            return scraper.parse_performer_by_url(url_info)
    else:
        sys.stderr.write(f"No scraper found for domain: {domain}\n")
        sys.exit(-1)


if __name__ == "__main__":
    info = json.loads(sys.stdin.read())

    if sys.argv[1] == "performerByURL":
        result = performer_by_url(info)
        print(json.dumps(result, ensure_ascii=False))
