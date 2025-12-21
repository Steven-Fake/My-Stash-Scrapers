import json
import random
import sys
from urllib.parse import urljoin

import requests

from config import BASE_URL
from model import WD14Tagger
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

    model = WD14Tagger()

    # choose random 10 images and generate tags
    tags = set()

    for image_id in random.choices(list(range(image_count)), k=min(10, image_count)):
        resp = requests.get(
            url=urljoin(BASE_URL, f"/gallery/{gallery_id}/preview/{image_id}"),
            headers={"ApiKey": api_key}
        )
        if resp.status_code != 200:
            continue
        data = resp.content
        try:
            predict_tags = model.predict(data)
            for tag in predict_tags:
                tags.add(tag)
        except Exception as e:
            continue
    scraped_tags: list[ScrapedTag] = [ScrapedTag(name=t) for t in tags]

    print(json.dumps(ScrapedGallery(tags=scraped_tags), ensure_ascii=False))
