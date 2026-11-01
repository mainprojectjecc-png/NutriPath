
import { useState } from "react";
import { Plus, Send, Leaf } from "lucide-react";

const initialMeals = [
  { type: "Breakfast", time: "8:00 AM", name: "Oats and Banana", detail: "Oats, banana, milk", calories: 320, emoji: "🥣" },
  { type: "Lunch", time: "1:00 PM", name: "Healthy Veg Rice", detail: "Rice, vegetables, dal", calories: 450, emoji: "🥗" },
  { type: "Snack", time: "4:30 PM", name: "Fruit and Nuts", detail: "Apple and almonds", calories: 180, emoji: "🍎" },
  { type: "Dinner", time: "7:30 PM", name: "Chapati and Paneer", detail: "Whole wheat chapati, paneer", calories: 380, emoji: "🍽️" }
];

export default function MealPlanner() {
  const [meals, setMeals] = useState(initialMeals);
  const [food, setFood] = useState("");
  const [reason, setReason] = useState("");
  const [message, setMessage] = useState("");

  const total = meals.reduce((sum, meal) => sum + meal.calories, 0);

  function addMeal() {
    const name = prompt("Enter meal name:");
    if (!name?.trim()) return;

    const calories = Number(prompt("Enter estimated calories:", "200"));

    if (!Number.isFinite(calories) || calories < 0) {
      alert("Enter a valid calorie amount.");
      return;
    }

    setMeals(prev => [
      ...prev,
      {
        type: "Additional meal",
        time: "Custom",
        name,
        detail: "Custom meal entry",
        calories,
        emoji: "🥑"
      }
    ]);
  }

  function submitRequest(e) {
    e.preventDefault();

    if (!food.trim() || !reason) {
      setMessage("Please enter the food and select a reason.");
      return;
    }

    setMessage(`Request for ${food} submitted successfully (demo).`);
    setFood("");
    setReason("");
  }

  return (
    <>
      <div className="page-title-row">
        <div>
          <span className="eyebrow">NUTRITION MANAGEMENT</span>
          <h1>Meal Planner</h1>
          <p>Plan balanced meals and make healthier food choices.</p>
        </div>
        <button className="primary-button" onClick={addMeal}>
          <Plus size={17} /> Add meal
        </button>
      </div>

      <div className="meal-summary">
        <div>
          <span>Today's planned calories</span>
          <h2>{total} <small>kcal</small></h2>
          <p>Sample daily target: 1,800 kcal</p>
        </div>
        <div className="hero-art">🥑</div>
      </div>

      <div className="section-heading">
        <div>
          <h2>Your meal schedule</h2>
          <p>A balanced meal plan for your day.</p>
        </div>
      </div>

      <div className="planned-meals">
        {meals.map((meal, index) => (
          <div className="planned-meal" key={`${meal.name}-${index}`}>
            <div className="food-emoji">{meal.emoji}</div>
            <div className="meal-info">
              <span className="meal-type">{meal.type} · {meal.time}</span>
              <strong>{meal.name}</strong>
              <small>{meal.detail}</small>
            </div>
            <div className="meal-right">
              <strong>{meal.calories} kcal</strong>
              <span>Estimated</span>
            </div>
          </div>
        ))}
      </div>

      <div className="section-heading">
        <div>
          <h2>Food replacement request</h2>
          <p>Request alternatives for foods that don't suit your preferences.</p>
        </div>
      </div>

      <form className="panel request-form" onSubmit={submitRequest}>
        <label>Food you want to replace</label>
        <input
          value={food}
          onChange={e => setFood(e.target.value)}
          placeholder="Example: Milk, rice, eggs..."
        />

        <label>Reason for replacement</label>
        <select value={reason} onChange={e => setReason(e.target.value)}>
          <option value="">Select a reason</option>
          <option>Food preference</option>
          <option>Allergy or intolerance</option>
          <option>Not available</option>
          <option>Other</option>
        </select>

        <button className="primary-button" type="submit">
          <Send size={16} /> Submit request
        </button>

        {message && <p className="form-message">{message}</p>}
      </form>

      <div className="recommendation">
        <Leaf size={24} />
        <div>
          <strong>Healthy eating reminder</strong>
          <p>Include protein, fibre and a variety of vegetables in your daily meals.</p>
        </div>
      </div>
    </>
  );
}
