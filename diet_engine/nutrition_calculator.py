
def calculate_bmi(weight_kg: float, height_cm: float) -> dict:
    """
    Calculate Body Mass Index (BMI).

    Weight is given in kilograms and height in centimetres.
    """

    if weight_kg <= 0:
        raise ValueError("Weight must be greater than zero.")

    if height_cm <= 0:
        raise ValueError("Height must be greater than zero.")

    height_m = height_cm / 100
    bmi = weight_kg / (height_m ** 2)

    if bmi < 18.5:
        category = "Underweight"
    elif bmi < 25:
        category = "Normal weight"
    elif bmi < 30:
        category = "Overweight"
    else:
        category = "Obesity"

    return {
        "weight_kg": weight_kg,
        "height_cm": height_cm,
        "bmi": round(bmi, 2),
        "category": category
    }


def calculate_daily_calories(
    weight_kg: float,
    height_cm: float,
    age: int,
    gender: str,
    activity_factor: float = 1.2
) -> dict:
    """
    Estimate daily maintenance calories using the
    Mifflin-St Jeor equation.

    This is an approximate adult estimate, not medical advice.
    """

    if weight_kg <= 0:
        raise ValueError("Weight must be greater than zero.")

    if height_cm <= 0:
        raise ValueError("Height must be greater than zero.")

    if age <= 0:
        raise ValueError("Age must be greater than zero.")

    if activity_factor <= 0:
        raise ValueError("Activity factor must be positive.")

    gender = gender.lower()

    if gender not in ["male", "female"]:
        raise ValueError("Gender must be male or female.")

    # Calculate Basal Metabolic Rate (BMR)
    if gender == "male":
        bmr = (
            10 * weight_kg
            + 6.25 * height_cm
            - 5 * age
            + 5
        )
    else:
        bmr = (
            10 * weight_kg
            + 6.25 * height_cm
            - 5 * age
            - 161
        )

    # Estimate daily maintenance calories
    daily_calories = bmr * activity_factor

    return {
        "bmr": round(bmr, 2),
        "estimated_daily_calories": round(daily_calories, 2),
        "activity_factor": activity_factor,
        "note": "Approximate adult estimate for general information only."
    }
