from typing import TypedDict, Optional, Literal


class PerformerByURLInput(TypedDict):
    url: str


class PerformerByURLOutput(TypedDict, total=False):
    name: Optional[str]
    aliases: Optional[str]
    birthdate: Optional[str]
    urls: Optional[list[str]]
    details: Optional[str]
    image: Optional[str]
    height: Optional[str]  # cm
    weight: Optional[str]  # kg
    measurements: Optional[str]
    tags: Optional[list[dict[Literal["name"], str]]]
