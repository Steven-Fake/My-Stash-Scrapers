import json
import random
import sys
from urllib.parse import urljoin

import requests

from config import BASE_URL
from model import load, predict
from py_common.graphql import configuration, callGraphQL
from py_common.types import ScrapedGallery, ScrapedTag

if __name__ == "__main__":
    info = json.loads(sys.stdin.read())

    config = configuration()
    gallery_id = info.get("id")
    image_count: int = callGraphQL(
        'query { findGallery(id: "' + gallery_id + '") { image_count } }'
    ).get("findGallery", {}).get("image_count")
    api_key = config.get("general", {}).get("apiKey")

    # choose random 10 images and generate tags
    images = []
    for image_id in random.choices(list(range(image_count)), k=min(10, image_count)):
        resp = requests.get(
            url=urljoin(BASE_URL, f"/gallery/{gallery_id}/preview/{image_id}"),
            headers={"ApiKey": api_key}
        )
        if resp.status_code != 200:
            continue
        images.append(resp.content)
    session, tags_df = load()
    res = predict(session, tags_df, images)
    scraped_tags: list[ScrapedTag] = [ScrapedTag(name=t[0]) for t in res]

    print(json.dumps(ScrapedGallery(tags=scraped_tags), ensure_ascii=False))
