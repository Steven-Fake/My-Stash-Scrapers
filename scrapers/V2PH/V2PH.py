import json
import sys
from urllib.request import getproxies
import re
from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag
from cloudscraper import create_scraper


def parse_performer_by_url(url_info: dict):
    url = url_info.get("url")
    if not url:
        sys.stderr.write("No URL provided\n")
        sys.exit(-1)
    resp = create_scraper().get(
        url,
        headers={'accept-language': 'zh-CN,zh;q=0.9'},
        proxies=getproxies()
    )
    if resp.status_code != 200:
        sys.stderr.write("Failed to retrieve URL\n")
        sys.exit(-1)

    soup = BeautifulSoup(resp.content, "html.parser")

    info_elem = soup.select_one("div.row.card-body")
    if not info_elem:
        sys.stderr.write("No performer info found\n")
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

    last_child_elem = [i for i in info_elem.contents if isinstance(i, Tag)][-1]
    for string_elem in reversed(last_child_elem.contents):
        if isinstance(string_elem, NavigableString) and string_elem.strip():
            last_text = string_elem.strip()
            break
    else:
        last_text = ""

    return {
        "name": name,
        "aliases": ",".join(aliases),
        "image": image_url,
        "birthdate": birthdate,
        "height": height,
        "measurements": measurements,
        "urls": urls,
        "details": last_text
    }


if __name__ == "__main__":
    info = json.loads(sys.stdin.read())
    
    if sys.argv[1] == "performerByURL":
        result = parse_performer_by_url(info)
        print(json.dumps(result, ensure_ascii=False))
