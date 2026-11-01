
import unittest

from diet_engine import (
    calculate_weight_change,
    generate_monthly_journey,
    generate_daily_meals,
    suggest_food_replacements,
    calculate_bmi,
    calculate_daily_calories,
)


class TestDietEngine(unittest.TestCase):

    def test_weight_calculation(self):
        result = calculate_weight_change(75, 65)
        self.assertEqual(result["weight_difference_kg"], -10)
        self.assertEqual(result["goal"], "weight_loss")

    def test_invalid_weight(self):
        with self.assertRaises(ValueError):
            calculate_weight_change(0, 65)

    def test_monthly_journey(self):
        result = generate_monthly_journey(
            75, 65, "2026-11-01", 3
        )
        self.assertEqual(len(result["milestones"]), 4)
        self.assertEqual(
            result["milestones"][-1]["target_weight_kg"], 65
        )

    def test_daily_meals(self):
        preferences = {
            "diet_type": "vegetarian",
            "allergies": []
        }
        result = generate_daily_meals(
            preferences, "2026-11-01"
        )
        self.assertIn("breakfast", result["meals"])
        self.assertIn("lunch", result["meals"])

    def test_invalid_diet(self):
        preferences = {
            "diet_type": "unknown",
            "allergies": []
        }
        with self.assertRaises(ValueError):
            generate_daily_meals(preferences, "2026-11-01")

    def test_food_replacement(self):
        preferences = {
            "diet_type": "vegetarian",
            "allergies": []
        }
        result = suggest_food_replacements(
            "white rice", preferences
        )
        self.assertTrue(len(result) > 0)
        self.assertEqual(result[0]["name"], "Brown rice")
        
    def test_bmi_calculation(self):
        result = calculate_bmi(70, 175)
        self.assertEqual(result["bmi"], 22.86)
        self.assertEqual(result["category"], "Normal weight")

    def test_bmi_categories(self):
        self.assertEqual(calculate_bmi(45, 170)["category"], "Underweight")
        self.assertEqual(calculate_bmi(65, 170)["category"], "Normal weight")
        self.assertEqual(calculate_bmi(80, 170)["category"], "Overweight")
        self.assertEqual(calculate_bmi(90, 170)["category"], "Obesity")

    def test_invalid_bmi_input(self):
        with self.assertRaises(ValueError):
            calculate_bmi(0, 175)

        with self.assertRaises(ValueError):
            calculate_bmi(70, 0)

    def test_daily_calories_male(self):
        result = calculate_daily_calories(70, 175, 25, "male")
        self.assertEqual(result["bmr"], 1673.75)
        self.assertEqual(result["estimated_daily_calories"], 2008.5)

    def test_daily_calories_female(self):
        result = calculate_daily_calories(70, 175, 25, "female")
        self.assertEqual(result["bmr"], 1507.75)
        self.assertEqual(result["estimated_daily_calories"], 1809.3)

    def test_invalid_calorie_input(self):
        with self.assertRaises(ValueError):
            calculate_daily_calories(0, 175, 25, "male")

        with self.assertRaises(ValueError):
            calculate_daily_calories(70, 175, 25, "unknown")
    


if __name__ == "__main__":
    unittest.main()
