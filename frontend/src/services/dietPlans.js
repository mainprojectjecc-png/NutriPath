import api from "./api";

export function generateDietPlan(StartDate, Days) {
  return api.post("/api/v1/diet-plans/generate", { StartDate, Days });
}

export function saveDietPlan(plan) {
  return api.post("/api/v1/diet-plans/", plan);
}

export function getDietPlans() {
  return api.get("/api/v1/diet-plans/");
}

export function updateDietPlan(id, updates) {
  return api.put(`/api/v1/diet-plans/${id}`, updates);
}
