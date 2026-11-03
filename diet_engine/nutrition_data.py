
import csv
from pathlib import Path

DATASET_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "nutrition_dataset.csv"
)


def load_food_data():
    """Load nutrition information from the CSV dataset."""

    with open(DATASET_PATH, "r", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        foods = list(reader)

    return foods


def get_food_nutrition(food_name: str):
    """Find nutrition information for a food by name."""

    foods = load_food_data()

    for food in foods:
        if food["food_name"].strip().lower() == food_name.strip().lower():
            return food

    return None
