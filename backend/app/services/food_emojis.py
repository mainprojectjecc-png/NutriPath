import json
from pathlib import Path
from typing import TypedDict


_FOOD_METADATA_PATH = Path(__file__).resolve().parents[3] / "shared" / "food_emojis.json"


class FoodMetadata(TypedDict):
    emoji: str
    servingGrams: int
    servingLabel: str


FOOD_METADATA_BY_ID: dict[str, FoodMetadata] = json.loads(
    _FOOD_METADATA_PATH.read_text(encoding="utf-8")
)
FOOD_EMOJI_BY_ID = {
    food_id: metadata["emoji"]
    for food_id, metadata in FOOD_METADATA_BY_ID.items()
}
DEFAULT_FOOD_EMOJI = "🥗"


def get_canonical_food_emoji(food_id: str | None) -> str | None:
    if not food_id:
        return None
    metadata = FOOD_METADATA_BY_ID.get(food_id.strip().casefold())
    return metadata["emoji"] if metadata else None


def get_canonical_food_serving(food_id: str | None) -> tuple[str, float] | None:
    if not food_id:
        return None
    metadata = FOOD_METADATA_BY_ID.get(food_id.strip().casefold())
    if not metadata:
        return None
    return metadata["servingLabel"], float(metadata["servingGrams"])


def is_corrupted_emoji(value: str) -> bool:
    return not value or "?" in value or "\ufffd" in value
