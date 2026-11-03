import foodMetadata from "../../../../shared/food_emojis.json";

export const foodCatalog = [
  { id: "idli", name: "Idli", category: "Breakfast", calories: 58, protein: 2, carbs: 12, fats: 0.2 },
  { id: "masala-dosa", name: "Masala dosa", category: "Breakfast", calories: 290, protein: 6, carbs: 44, fats: 10 },
  { id: "poha", name: "Poha", category: "Breakfast", calories: 250, protein: 5, carbs: 42, fats: 7 },
  { id: "upma", name: "Upma", category: "Breakfast", calories: 220, protein: 6, carbs: 38, fats: 5 },
  { id: "plain-dosa", name: "Plain dosa", category: "Breakfast", calories: 168, protein: 4, carbs: 29, fats: 4 },
  { id: "paratha", name: "Aloo paratha", category: "Breakfast", calories: 260, protein: 6, carbs: 38, fats: 9 },
  { id: "besan-chilla", name: "Besan chilla", category: "Breakfast", calories: 180, protein: 9, carbs: 22, fats: 6 },
  { id: "oats", name: "Oats porridge", category: "Breakfast", calories: 160, protein: 6, carbs: 27, fats: 4 },
  { id: "chapati", name: "Chapati", category: "Lunch", calories: 120, protein: 3, carbs: 20, fats: 3 },
  { id: "brown-rice", name: "Cooked brown rice", category: "Lunch", calories: 165, protein: 4, carbs: 35, fats: 1.4 },
  { id: "white-rice", name: "Cooked white rice", category: "Lunch", calories: 195, protein: 4, carbs: 43, fats: 0.4 },
  { id: "dal", name: "Dal tadka", category: "Lunch", calories: 190, protein: 11, carbs: 25, fats: 5 },
  { id: "rajma", name: "Rajma curry", category: "Lunch", calories: 210, protein: 12, carbs: 32, fats: 4 },
  { id: "chole", name: "Chole", category: "Lunch", calories: 240, protein: 12, carbs: 34, fats: 7 },
  { id: "paneer", name: "Paneer bhurji", category: "Lunch", calories: 265, protein: 18, carbs: 9, fats: 18 },
  { id: "palak-paneer", name: "Palak paneer", category: "Lunch", calories: 280, protein: 15, carbs: 14, fats: 19 },
  { id: "mixed-veg", name: "Mixed vegetable sabzi", category: "Lunch", calories: 140, protein: 4, carbs: 19, fats: 6 },
  { id: "curd", name: "Plain curd", category: "Lunch", calories: 92, protein: 5, carbs: 7, fats: 5 },
  { id: "samosa", name: "Samosa", category: "Snacks", calories: 190, protein: 4, carbs: 23, fats: 9 },
  { id: "dhokla", name: "Dhokla", category: "Snacks", calories: 160, protein: 7, carbs: 25, fats: 4 },
  { id: "roasted-chana", name: "Roasted chana", category: "Snacks", calories: 120, protein: 6, carbs: 18, fats: 2 },
  { id: "makhana", name: "Roasted makhana", category: "Snacks", calories: 90, protein: 3, carbs: 17, fats: 1 },
  { id: "banana", name: "Banana", category: "Snacks", calories: 105, protein: 1.3, carbs: 27, fats: 0.4 },
  { id: "apple", name: "Apple", category: "Snacks", calories: 95, protein: 0.5, carbs: 25, fats: 0.3 },
  { id: "almonds", name: "Almonds", category: "Snacks", calories: 164, protein: 6, carbs: 6, fats: 14 },
  { id: "sprouts", name: "Moong sprouts chaat", category: "Snacks", calories: 130, protein: 10, carbs: 22, fats: 1 },
  { id: "chicken-curry", name: "Chicken curry", category: "Dinner", calories: 290, protein: 27, carbs: 8, fats: 16 },
  { id: "grilled-chicken", name: "Grilled chicken", category: "Dinner", calories: 248, protein: 39, carbs: 0, fats: 9 },
  { id: "tofu", name: "Tofu bhurji", category: "Dinner", calories: 190, protein: 18, carbs: 8, fats: 10 },
  { id: "khichdi", name: "Moong dal khichdi", category: "Dinner", calories: 260, protein: 11, carbs: 45, fats: 5 },
  { id: "roti", name: "Whole wheat roti", category: "Dinner", calories: 110, protein: 3.5, carbs: 22, fats: 1 },
  { id: "raita", name: "Vegetable raita", category: "Dinner", calories: 100, protein: 5, carbs: 10, fats: 4 }
].map(food => ({ ...food, ...foodMetadata[food.id] }));

function catalogKey(value) {
  return String(value || "").trim().toLocaleLowerCase();
}

function getServingGrams(servingSize, fallback = 100) {
  const grams = servingSize.match(/(\d+(?:\.\d+)?)\s*(?:g|grams?)\b/i);
  const value = grams ? Number(grams[1]) : fallback;
  return Number.isFinite(value) && value > 0 ? value : fallback;
}

export function getFoodOptions(items) {
  const catalogById = new Map(foodCatalog.map(food => [catalogKey(food.id), food]));
  const serverFoodsByCatalogId = new Map();
  const additionalFoods = [];

  items.forEach(item => {
    const catalogFood = catalogById.get(catalogKey(item.CatalogID));
    if (catalogFood) {
      serverFoodsByCatalogId.set(catalogKey(item.CatalogID), item);
      return;
    }

    const servingSize = item.ServingSize || "100 g";
    additionalFoods.push({
      id: item.CatalogID || `food-${item.FoodID}`,
      name: item.FoodName,
      category: item.Category || "",
      emoji: "🥗",
      servingGrams: getServingGrams(servingSize),
      servingLabel: servingSize,
      calories: Number(item.Calories),
      protein: Number(item.Protein),
      carbs: Number(item.Carbs),
      fats: Number(item.Fat)
    });
  });

  const builtInFoods = foodCatalog.map(food => {
    const item = serverFoodsByCatalogId.get(catalogKey(food.id));
    if (!item) return food;
    return {
      ...food,
      name: item.FoodName,
      category: item.Category || food.category,
      servingGrams: getServingGrams(item.ServingSize || food.servingLabel, food.servingGrams),
      servingLabel: item.ServingSize || food.servingLabel,
      calories: Number(item.Calories),
      protein: Number(item.Protein),
      carbs: Number(item.Carbs),
      fats: Number(item.Fat)
    };
  });

  return [...builtInFoods, ...additionalFoods];
}

export const mealTypes = ["Breakfast", "Lunch", "Snacks", "Dinner"];

export function getCanonicalFoodEmoji(foodId) {
  return foodMetadata[String(foodId || "").trim().toLocaleLowerCase()]?.emoji || null;
}
