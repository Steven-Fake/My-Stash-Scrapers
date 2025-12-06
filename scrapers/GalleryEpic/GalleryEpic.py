import json
import sys
from urllib.request import getproxies
import requests
from bs4 import BeautifulSoup


def parse_performer_by_url(url_info: dict):
    url = url_info.get("url")
    if not url:
        sys.stderr.write("No URL provided\n")
        sys.exit(-1)
    resp = requests.get(url, proxies=getproxies())
    if resp.status_code != 200:
        sys.stderr.write("Failed to retrieve URL\n")
        sys.exit(-1)

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

    return {
        "name": name,
        "urls": urls,
        "image": avatar_url
    }


if __name__ == "__main__":
    info = json.loads(sys.stdin.read())
    
    if sys.argv[1] == "performerByURL":
        result = parse_performer_by_url(info)
        print(json.dumps(result, ensure_ascii=False))
