
from diet_engine import (
    calculate_weight_change,
    generate_monthly_journey,
    generate_daily_meals,
    suggest_food_replacements,
)

# Test 1: Weight calculation
print("\n--- Weight Calculation ---")
print(calculate_weight_change(75, 65))

# Test 2: Monthly journey
print("\n--- Monthly Journey ---")
print(generate_monthly_journey(
    75, 65, "2026-11-01", 3
))

# Test 3: Daily meals
print("\n--- Daily Meals ---")
preferences = {
    "diet_type": "vegetarian",
    "allergies": []
}
print(generate_daily_meals(preferences, "2026-11-01"))

# Test 4: Food replacement
print("\n--- Food Replacement ---")
print(suggest_food_replacements("white rice", preferences))

print("\nAll tests executed!")
