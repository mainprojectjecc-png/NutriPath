import re
from collections.abc import Iterable
from typing import Any


ALLERGEN_ALIASES = {
    "peanut": ("peanut", "groundnut"),
    "tree nuts": (
        "tree nut",
        "almond",
        "walnut",
        "cashew",
        "pecan",
        "pistachio",
        "hazelnut",
        "brazil nut",
        "macadamia",
    ),
    "milk and dairy": ("milk", "dairy", "lactose", "casein", "whey"),
    "egg": ("egg",),
    "soy": ("soy", "soya", "soybean"),
    "wheat and gluten": ("wheat", "gluten", "barley", "rye", "spelt"),
    "fish": ("fish", "anchovy", "salmon", "tuna", "cod", "sardine"),
    "shellfish": (
        "shellfish",
        "crustacean",
        "mollusk",
        "mussel",
        "oyster",
        "shrimp",
        "prawn",
        "crab",
        "lobster",
    ),
    "sesame": ("sesame", "tahini"),
    "meat": ("meat", "poultry", "beef", "pork", "chicken", "lamb", "mutton"),
    "animal-derived ingredients": (
        "animal-derived",
        "gelatin",
        "lard",
        "tallow",
        "shellac",
        "honey",
    ),
}

_LEADING_RESTRICTION_WORDS = re.compile(
    r"^(?:(?:i\s+)?(?:am\s+)?(?:allergic\s+to|intolerant\s+to|avoid|avoids|"
    r"cannot\s+eat|can't\s+eat|do\s+not\s+eat|don't\s+eat|no|without)\s+)+",
    re.IGNORECASE,
)


def _contains_phrase(text: str, phrase: str) -> bool:
    plural_suffix = "" if phrase.endswith(("s", "y")) else "s?"
    return bool(
        re.search(
            rf"(?<![a-z0-9]){re.escape(phrase.casefold())}{plural_suffix}(?![a-z0-9])",
            text.casefold(),
        )
    )


def _restriction_terms(values: Iterable[str | None]) -> tuple[set[str], set[str]]:
    categories: set[str] = set()
    custom_terms: set[str] = set()
    for value in values:
        if not value:
            continue
        for segment in re.split(r"[,;\n|]+", value.casefold()):
            segment = _LEADING_RESTRICTION_WORDS.sub("", segment.strip())
            if not segment:
                continue
            matches = {
                category
                for category, aliases in ALLERGEN_ALIASES.items()
                if any(_contains_phrase(segment, alias) for alias in aliases)
            }
            if matches:
                categories.update(matches)
            else:
                cleaned = re.sub(r"[^a-z0-9 -]", " ", segment)
                cleaned = re.sub(r"\s+", " ", cleaned).strip()
                if cleaned and cleaned not in {"other", "none", "n a"}:
                    custom_terms.add(cleaned)
    return categories, custom_terms


def _metadata_text(value: Any) -> str:
    return value.casefold() if isinstance(value, str) else ""


def metadata_is_complete(metadata: Any) -> bool:
    return bool(
        metadata is not None
        and metadata.IsVerified is True
        and isinstance(metadata.Ingredients, str)
        and metadata.Ingredients.strip()
        and metadata.Allergens is not None
        and metadata.CrossContactWarnings is not None
        and isinstance(metadata.VerificationSource, str)
        and metadata.VerificationSource.strip()
        and metadata.VerifiedAt is not None
    )


def _contains_any_alias(text: str, categories: set[str]) -> bool:
    return any(
        _contains_phrase(text, alias)
        for category in categories
        for alias in ALLERGEN_ALIASES[category]
    )


def is_allergy_safe(metadata: Any, restrictions: Iterable[str | None]) -> bool:
    categories, custom_terms = _restriction_terms(restrictions)
    if not categories and not custom_terms:
        return True
    if not metadata_is_complete(metadata):
        return False

    allergen_text = _metadata_text(metadata.Allergens)
    ingredient_text = _metadata_text(metadata.Ingredients)
    cross_contact_text = _metadata_text(metadata.CrossContactWarnings)
    safety_text = " ".join((allergen_text, ingredient_text, cross_contact_text))
    if _contains_any_alias(safety_text, categories):
        return False
    return not any(_contains_phrase(safety_text, term) for term in custom_terms)


def is_food_avoided(
    food_name: str,
    metadata: Any,
    restrictions: Iterable[str | None],
) -> bool:
    categories, custom_terms = _restriction_terms(restrictions)
    if not categories and not custom_terms:
        return False
    if not metadata_is_complete(metadata):
        return True
    match_text = " ".join(
        (
            food_name.casefold(),
            _metadata_text(metadata.Ingredients),
            _metadata_text(metadata.Allergens),
        )
    )
    return _contains_any_alias(match_text, categories) or any(
        _contains_phrase(match_text, term) for term in custom_terms
    )


def is_diet_eligible(metadata: Any, preference: str) -> bool:
    if preference in {"", "no preference", "omnivore"}:
        return True
    if not metadata_is_complete(metadata):
        return False

    if preference == "vegetarian":
        return (
            metadata.IsVegetarian is True
            and metadata.ContainsMeat is False
            and metadata.ContainsFish is False
            and metadata.ContainsSeafood is False
        )
    if preference == "vegan":
        return (
            metadata.IsVegan is True
            and metadata.ContainsEgg is False
            and metadata.ContainsDairy is False
            and metadata.ContainsHoney is False
            and metadata.ContainsFish is False
            and metadata.ContainsSeafood is False
            and metadata.ContainsMeat is False
            and metadata.AnimalDerivedIngredients is not None
            and not metadata.AnimalDerivedIngredients.strip()
        )
    if preference == "eggetarian":
        return (
            metadata.IsVegetarian is True
            and metadata.ContainsMeat is False
            and metadata.ContainsFish is False
            and metadata.ContainsSeafood is False
        )
    if preference == "pescatarian":
        return (
            metadata.ContainsMeat is False
            and (
                metadata.IsVegetarian is True
                or metadata.ContainsFish is True
                or metadata.ContainsSeafood is True
            )
        )
    return preference == "other"


def restrictions_match_catalog(
    restrictions: Iterable[str | None],
    searchable_values: Iterable[str],
) -> bool:
    categories, custom_terms = _restriction_terms(restrictions)
    text = " ".join(value.casefold() for value in searchable_values)
    return (
        _contains_any_alias(text, categories)
        or any(_contains_phrase(text, term) for term in custom_terms)
    )
