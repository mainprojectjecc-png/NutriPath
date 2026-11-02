import api from "./api";
import { loadMealTrackerData } from "./mealTracker";

function migrationKey(userId) {
  return `nutripath.nutrition-api-migration.v1.${userId}`;
}

export async function getNutritionData(userId) {
  let data = await api.get("/api/nutrition");
  const key = migrationKey(userId);
  if (localStorage.getItem(key)) return data;

  const previous = loadMealTrackerData(userId);
  const hasServerLogs = data.meals.length > 0 || Object.keys(data.waterByDate).length > 0;
  const hasPreviousData = previous.meals.length > 0 ||
    Object.keys(previous.waterByDate).length > 0 ||
    previous.calorieGoal !== 2000 ||
    previous.waterGoal !== 2500;
  if (!hasServerLogs && hasPreviousData) {
    for (const meal of previous.meals) {
      await api.post("/api/nutrition/meals", {
        food_id: meal.foodId || meal.food_id,
        food_name: meal.foodName || meal.food_name,
        emoji: meal.emoji || "🥗",
        meal_type: meal.mealType || meal.meal_type,
        quantity: meal.quantity,
        serving_label: meal.servingLabel || meal.serving_label,
        serving_grams: meal.servingGrams || meal.serving_grams,
        calories: meal.calories,
        protein: meal.protein,
        carbs: meal.carbs,
        fats: meal.fats,
        date: meal.date
      });
    }
    for (const [date, amount] of Object.entries(previous.waterByDate)) {
      if (amount > 0) await api.post("/api/nutrition/water", { amount_ml: amount, date });
    }
    await api.put("/api/nutrition/settings", {
      calorie_goal: previous.calorieGoal,
      water_goal: previous.waterGoal
    });
    data = await api.get("/api/nutrition");
  }

  localStorage.setItem(key, "true");
  return data;
}

export function addFoodEntry(food, date) {
  return api.post("/api/nutrition/meals", {
    food_id: food.foodId,
    food_name: food.foodName,
    emoji: food.emoji,
    meal_type: food.mealType,
    quantity: food.quantity,
    serving_label: food.servingLabel,
    serving_grams: food.servingGrams,
    calories: food.calories,
    protein: food.protein,
    carbs: food.carbs,
    fats: food.fats,
    date
  });
}

export function removeFoodEntry(id) {
  return api.delete(`/api/nutrition/meals/${id}`);
}

export function addWaterEntry(date, amount) {
  return api.post("/api/nutrition/water", { date, amount_ml: amount });
}

export function saveNutritionSettings(data) {
  return api.put("/api/nutrition/settings", {
    calorie_goal: data.calorieGoal,
    water_goal: data.waterGoal
  });
}
