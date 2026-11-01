from datetime import date


# Starter sample meal data.
# diet_types: vegetarian, vegan, eggetarian, non_vegetarian

MEALS = [
    {
        "name": "Oats with banana",
        "type": "breakfast",
        "diet_types": ["vegetarian", "vegan", "eggetarian", "non_vegetarian"],
        "allergens": ["nuts"],
        "ingredients": ["oats", "banana", "milk"],
    },
    {
        "name": "Idli with sambar",
        "type": "breakfast",
        "diet_types": ["vegetarian", "vegan", "eggetarian", "non_vegetarian"],
        "allergens": [],
        "ingredients": ["idli", "sambar"],
    },
    {
        "name": "Vegetable rice with curd",
        "type": "lunch",
        "diet_types": ["vegetarian", "eggetarian", "non_vegetarian"],
        "allergens": ["dairy"],
        "ingredients": ["rice", "vegetables", "curd"],
    },
    {
        "name": "Vegetable rice",
        "type": "lunch",
        "diet_types": ["vegan"],
        "allergens": [],
        "ingredients": ["rice", "vegetables"],
    },
    {
        "name": "Chapati with dal",
        "type": "dinner",
        "diet_types": ["vegetarian", "vegan", "eggetarian", "non_vegetarian"],
        "allergens": ["gluten"],
        "ingredients": ["chapati", "dal"],
    },
    {
        "name": "Grilled chicken with vegetables",
        "type": "dinner",
        "diet_types": ["non_vegetarian"],
        "allergens": [],
        "ingredients": ["chicken", "vegetables"],
    },
    {
        "name": "Fruit bowl",
        "type": "snack",
        "diet_types": ["vegetarian", "vegan", "eggetarian", "non_vegetarian"],
        "allergens": [],
        "ingredients": ["seasonal fruits"],
    },
]


FOOD_REPLACEMENTS = [
    {
        "name": "Brown rice",
        "replaces": ["white rice"],
        "diet_types": ["vegetarian", "vegan", "eggetarian", "non_vegetarian"],
        "allergens": [],
        "reason": "A whole-grain alternative.",
    },
    {
        "name": "Curd",
        "replaces": ["mayonnaise"],
        "diet_types": ["vegetarian", "eggetarian", "non_vegetarian"],
        "allergens": ["dairy"],
        "reason": "A simple dairy-based alternative.",
    },
    {
        "name": "Tofu",
        "replaces": ["paneer"],
        "diet_types": ["vegan", "vegetarian"],
        "allergens": ["soy"],
        "reason": "A plant-based protein alternative.",
    },
    {
        "name": "Fruit bowl",
        "replaces": ["packaged sweets"],
        "diet_types": ["vegetarian", "vegan", "eggetarian", "non_vegetarian"],
        "allergens": [],
        "reason": "A fruit-based alternative.",
    },
]


def _is_suitable(item: dict, diet_type: str, allergies: list) -> bool:
    """Check dietary preference and allergy restrictions."""

    if diet_type not in item["diet_types"]:
        return False

    item_allergens = {
        allergen.lower() for allergen in item["allergens"]
    }

    user_allergies = {
        allergy.lower() for allergy in allergies
    }

    return item_allergens.isdisjoint(user_allergies)


def generate_daily_meals(
    user_preferences: dict,
    meal_date: str,
) -> dict:
    """
    Generate a sample daily meal plan.

    Example preferences:
    {
        "diet_type": "vegetarian",
        "allergies": ["nuts"]
    }
    """

    try:
        selected_date = date.fromisoformat(meal_date)
    except (TypeError, ValueError):
        raise ValueError("meal_date must use YYYY-MM-DD format.")

    diet_type = user_preferences.get("diet_type", "vegetarian").lower()
    allergies = user_preferences.get("allergies", [])

    valid_diets = {
        "vegetarian",
        "vegan",
        "eggetarian",
        "non_vegetarian",
    }

    if diet_type not in valid_diets:
        raise ValueError("Unsupported diet type.")

    if not isinstance(allergies, list):
        raise ValueError("Allergies must be provided as a list.")

    selected_meals = {}

    for meal_type in ["breakfast", "lunch", "dinner", "snack"]:
        options = [
            meal for meal in MEALS
            if meal["type"] == meal_type
            and _is_suitable(meal, diet_type, allergies)
        ]

        if options:
            selected_meals[meal_type] = options[0]

    return {
        "date": selected_date.isoformat(),
        "diet_type": diet_type,
        "meals": selected_meals,
        "note": (
            "Sample suggestions only. Check ingredients and "
            "allergen information before eating."
        ),
    }


def suggest_food_replacements(
    food_to_replace: str,
    preferences: dict,
) -> list:
    """Suggest alternatives based on dietary preferences."""

    diet_type = preferences.get("diet_type", "vegetarian").lower()
    allergies = preferences.get("allergies", [])

    food_name = food_to_replace.strip().lower()

    if not food_name:
        raise ValueError("Please provide a food name.")

    suggestions = []

    for item in FOOD_REPLACEMENTS:
        replaces_food = [
            food.lower() for food in item["replaces"]
        ]

        if (
            food_name in replaces_food
            and _is_suitable(item, diet_type, allergies)
        ):
            suggestions.append({
                "name": item["name"],
                "reason": item["reason"],
            })

    return suggestions