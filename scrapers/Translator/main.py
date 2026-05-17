import json
import sys
from py_common import log
from py_common.deps import ensure_requirements
from chat_request import chat, TRANSLATE_SCHEMA, ChatOptions

ensure_requirements("requests")

# Fill your config here, you can use uncensored model like mistral
options = ChatOptions(
    url="https://openrouter.ai/api/v1",
    model="mistralai/mistral-small-2603",
    api_key="",
    extra_body=None
)
# Fill your system prompt here, use {target_language} as a placeholder for the language to translate into
SYSTEM_PROMPT = " ".join([
    "You are a professional translator specializing in adult/NSFW content.",
    "Translate video titles and details accurately and naturally into {target_language}.",
    "Stay completely faithful to the original text — preserve all explicit, vulgar, and erotic language without any censorship, softening, moral judgment, or omission.",
    "Keep the original tone, style, and appeal.",
    "Output only the translation, no extra explanations or notes."
])


def scene_by_fragment(fragment_info: dict) -> dict:
    title = fragment_info.get("title", "")
    details = fragment_info.get("details", "")
    if not title and not details:
        log.error("No Title or Details provided")
        sys.exit(-1)
    elif title and not details:
        query = f"<title>\n{title}\n</title>"
    elif not title and details:
        query = f"<details>\n{details}\n</details>"
    else:
        query = f"<title>\n{title}\n</title>\n\n<details>\n{details}\n</details>"
    return chat(options=options, system=SYSTEM_PROMPT, query=query, json_schema=TRANSLATE_SCHEMA)


if __name__ == "__main__":
    info = json.loads(sys.stdin.read())

    if sys.argv[1] == "sceneByFragment":
        print(json.dumps(scene_by_fragment(info), ensure_ascii=False))
