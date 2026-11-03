import { mockRequests } from "../mock/coachMockData";

const USE_MOCK = true; // change to false on Day 3
const BASE = "http://localhost:8000/api/v1";

// In-memory copy so mock changes survive between clicks
let db = mockRequests.map((r) => ({ ...r }));

const delay = (value) => new Promise((resolve) => setTimeout(() => resolve(value), 300));

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(`Request failed (${res.status})`);
  return res.json();
}

export async function getCoachRequests() {
  if (USE_MOCK) return delay(db.map((r) => ({ ...r })));
  return request("/coach/requests");
}

export async function sendSuggestion(id, suggestion) {
  if (USE_MOCK) {
    const item = db.find((r) => r.id === id);
    if (!item) throw new Error("Request not found");
    if (item.status !== "pending") throw new Error("Only pending requests can get a suggestion");
    item.suggestion = suggestion;
    item.status = "suggested";
    return delay({ ...item });
  }
  return request(`/coach/requests/${id}/suggestion`, {
    method: "POST",
    body: JSON.stringify({ suggestion }),
  });
}

export async function respondToSuggestion(id, accepted) {
  if (USE_MOCK) {
    const item = db.find((r) => r.id === id);
    if (!item) throw new Error("Request not found");
    if (item.status !== "suggested") throw new Error("Only suggested requests can be answered");
    item.status = accepted ? "accepted" : "rejected";
    return delay({ ...item });
  }
  const action = accepted ? "accept" : "reject";
  return request(`/food-change-requests/${id}/${action}`, { method: "POST" });
}