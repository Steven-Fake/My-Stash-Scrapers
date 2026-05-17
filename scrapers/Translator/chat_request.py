import json
from typing import TypedDict, Optional
from urllib import parse

import requests


class ChatOptions(TypedDict):
    url: str
    model: str
    api_key: str
    extra_body: Optional[dict]


TRANSLATE_SCHEMA = {
    "name": "translate_information",
    "schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "details": {"type": "string"}
        },
        "required": []
    }
}


def chat(options: ChatOptions, system: str, query: str, json_schema: Optional[dict] = None):
    if url := options.get('url'):
        if url[-1] != "/":
            url += "/"
        if "chat/completions" not in url:
            url = parse.urljoin(url, "chat/completions")
    else:
        raise ValueError("URL is required for chat function")
    if model := options.get('model'):
        pass
    else:
        raise ValueError("Model is required for chat function")
    if api_key := options.get('api_key'):
        pass
    else:
        raise ValueError("API Key is required for chat function")

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": query}
        ],
        "extra_body": options.get("extra_body", {})
    }

    if json_schema:
        body["response_format"] = {
            "type": "json_schema",
            "json_schema": json_schema
        }
    req = requests.post(
        url=url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        data=json.dumps(body)
    )

    req.raise_for_status()
    result = req.json()

    structured_text = result["choices"][0]["message"]["content"]
    structured_data = json.loads(structured_text)

    return structured_data
