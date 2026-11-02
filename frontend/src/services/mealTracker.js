const STORAGE_KEY = "nutripath.daily-meal-tracker.v1";

const initialState = {
  meals: [],
  waterByDate: {},
  calorieGoal: 2000,
  waterGoal: 2500
};

function userStorageKey(userId) {
  return `${STORAGE_KEY}.${userId}`;
}

export function loadMealTrackerData(userId = "guest") {
  const scopedKey = userStorageKey(userId);
  let saved = window.localStorage.getItem(scopedKey);
  if (!saved && userId !== "guest" && !window.localStorage.getItem(`${STORAGE_KEY}.migration-complete`)) {
    const previousData = window.localStorage.getItem(STORAGE_KEY);
    window.localStorage.setItem(`${STORAGE_KEY}.migration-complete`, "true");
    if (previousData) {
      saved = previousData;
      window.localStorage.setItem(scopedKey, previousData);
    }
  }
  if (!saved) return initialState;

  const parsed = JSON.parse(saved);
  if (!parsed || typeof parsed !== "object" || !Array.isArray(parsed.meals)) {
    throw new Error("Saved meal tracker data is invalid. Clear this browser's saved NutriPath data to start fresh.");
  }

  return {
    meals: parsed.meals,
    waterByDate: parsed.waterByDate && typeof parsed.waterByDate === "object" ? parsed.waterByDate : {},
    calorieGoal: Number.isFinite(parsed.calorieGoal) && parsed.calorieGoal > 0 ? parsed.calorieGoal : initialState.calorieGoal,
    waterGoal: Number.isFinite(parsed.waterGoal) && parsed.waterGoal > 0 ? parsed.waterGoal : initialState.waterGoal
  };
}

export function saveMealTrackerData(data, userId = "guest") {
  window.localStorage.setItem(userStorageKey(userId), JSON.stringify(data));
}
