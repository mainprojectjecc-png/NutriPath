# Diet & Weight Planning Module

**Project:** NutriPath  
**Contributor:** Martha Vincy  
**Role:** Member 3 – Diet & Weight Planning (Python)

## 1. Overview

The Diet & Weight Planning module is an important component of NutriPath, an AI-powered personalized weight management platform.

The main purpose of this module is to help users plan and understand their weight management journey through basic nutrition calculations, weight goal planning, meal recommendations, and food replacement suggestions.

It is developed using Python with separate modules for nutrition calculations, weight management, and meal recommendations.

## 2. Objectives

- Calculate the user's Body Mass Index (BMI).
- Estimate daily calorie requirements.
- Help users identify their weight management goals.
- Generate monthly weight progress milestones.
- Recommend meals based on dietary preferences.
- Suggest healthier food alternatives.
- Provide a foundation for personalized diet planning.

## 3. Key Features

### 3.1 BMI Calculator

- Calculates BMI using the user's weight and height.
- Identifies the BMI category:
  - Underweight
  - Normal weight
  - Overweight
  - Obesity

### 3.2 Daily Calorie Calculator

- Estimates Basal Metabolic Rate (BMR).
- Uses the Mifflin-St Jeor equation.
- Estimates daily maintenance calories based on the user's activity level.
- Uses details such as weight, height, age, and gender.

### 3.3 Weight Goal Calculator

- Accepts current weight and target weight.
- Calculates the difference between current and target weight.
- Identifies whether the user wants to lose weight, gain weight, or maintain weight.

### 3.4 Monthly Weight Journey

- Generates monthly weight milestones.
- Uses the current weight, target weight, start date, and selected duration.
- Helps users understand their planned progress over time.

### 3.5 Daily Meal Recommendations

- Generates sample daily meal suggestions.
- Supports different dietary preferences:
  - Vegetarian
  - Vegan
  - Eggetarian
  - Non-vegetarian
- Filters meal suggestions using available allergen information.

### 3.6 Food Replacement Suggestions

- Suggests alternative food choices.
- Provides simple food replacement ideas.
- Supports healthier food selection as part of diet planning.

## 4. Technologies Used

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| Python Modules | Organizing the diet engine |
| unittest | Testing the functions |
| Git | Version control |
| GitHub | Project collaboration and code management |

## 5. Project Structure

\`\`\`text
diet_engine/
│
├── __init__.py
├── nutrition_calculator.py
├── weight_calculator.py
├── meal_recommendations.py
│
└── tests/
    └── test_diet_engine.py
\`\`\`

### File Description

- **__init__.py:** Makes the main diet engine functions available through the package.
- **nutrition_calculator.py:** Contains BMI and daily calorie calculation functions.
- **weight_calculator.py:** Contains weight goal calculations and monthly progress generation.
- **meal_recommendations.py:** Contains meal recommendation and food replacement functions.
- **tests/test_diet_engine.py:** Contains unit tests for checking the module's functionality.

## 6. Main Python Functions

| Function | Description |
|---|---|
| `calculate_bmi()` | Calculates BMI and identifies its category. |
| `calculate_daily_calories()` | Estimates BMR and daily calorie requirements. |
| `calculate_weight_change()` | Calculates the difference between current and target weight. |
| `generate_monthly_journey()` | Generates monthly weight milestones. |
| `generate_daily_meals()` | Suggests meals based on dietary preferences. |
| `suggest_food_replacements()` | Suggests alternative food choices. |

## 7. How to Run the Module

Run the commands from the main NutriPath project directory.

**Step 1: Clone the repository**

\`\`\`bash
git clone https://github.com/mainprojectjecc-png/NutriPath.git
\`\`\`

**Step 2: Open the project directory**

\`\`\`bash
cd NutriPath
\`\`\`

**Step 3: Switch to the Diet Engine branch**

\`\`\`bash
git checkout feature/diet-engine
\`\`\`

**Step 4: Run the sample program**

\`\`\`bash
python test_diet_engine.py
\`\`\`

**Step 5: Run the unit tests**

\`\`\`bash
python -m unittest discover -s diet_engine/tests -v
\`\`\`

## 8. Testing

The module includes unit tests to verify important functionalities, including:

- Weight change calculations.
- Invalid weight input handling.
- Monthly weight journey generation.
- Daily meal recommendations.
- Dietary preference validation.
- Food replacement suggestions.

The tests help ensure that the implemented functions work as expected.

## 9. Future Enhancements

- Expand the food and nutrition database.
- Include more personalized meal recommendations.
- Improve food filtering and dietary preference handling.
- Integrate the module with the NutriPath backend.
- Connect diet planning with the frontend.
- Add more advanced nutrition and progress tracking features.

## 10. Important Note

BMI and calorie calculations provide approximate estimates for general information. They are not medical diagnoses or personalized medical advice.

Meal recommendations currently use sample data. Allergen filtering does not guarantee food safety. Users should verify ingredients and consult qualified healthcare professionals for individual dietary requirements.

---

**Developed as part of the NutriPath project.**