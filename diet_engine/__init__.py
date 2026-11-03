from .weight_calculator import (
    calculate_weight_change,
    generate_monthly_journey,
)

from .meal_recommendations import (
    generate_daily_meals,
    suggest_food_replacements,
)

from .nutrition_calculator import (
    calculate_bmi,
    calculate_daily_calories,
)

__all__ = [
    "calculate_bmi",
    "calculate_daily_calories",
    "calculate_weight_change",
    "generate_monthly_journey",
    "generate_daily_meals",
    "suggest_food_replacements",
]