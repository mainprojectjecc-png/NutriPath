
import { useEffect, useMemo, useState } from "react";
import { ArrowUpRight, Leaf, Send } from "lucide-react";
import { getNutritionData } from "../services/nutrition";

function todayKey() {
  const today = new Date();
  return `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;
}

export default function MealPlanner({ userId, setActivePage }) {
  const [trackerData, setTrackerData] = useState(null);
  const [food, setFood] = useState("");
  const [reason, setReason] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    getNutritionData(userId)
      .then(setTrackerData)
      .catch(error => setMessage(error.message || "Your food journal could not be loaded."));
  }, [userId]);

  const meals = useMemo(() => trackerData?.meals.filter(meal => meal.date === todayKey()) || [], [trackerData]);
  const total = meals.reduce((sum, meal) => sum + meal.calories, 0);

  function submitRequest(e) {
    e.preventDefault();

    if (!food.trim() || !reason) {
      setMessage("Please enter the food and select a reason.");
      return;
    }

    setMessage("Food replacement requests are not connected to a service yet. Your request was not sent.");
  }

  return (
    <>
      <div className="page-title-row">
        <div>
          <span className="eyebrow">NUTRITION MANAGEMENT</span>
          <h1>Meal Planner</h1>
          <p>Plan balanced meals and make healthier food choices.</p>
        </div>
        <button className="primary-button" onClick={() => setActivePage("Daily Meal Tracker")}>
          <ArrowUpRight size={17} /> Log food
        </button>
      </div>

      <div className="meal-summary">
        <div>
          <span>Today's logged calories</span>
          <h2>{total} <small>kcal</small></h2>
          <p>Daily goal: {trackerData?.calorieGoal.toLocaleString() || "—"} kcal</p>
        </div>
        <div className="hero-art">🥑</div>
      </div>

      <div className="section-heading">
        <div>
          <h2>Meals logged today</h2>
          <p>Based on foods in your daily tracker.</p>
        </div>
      </div>

      <div className="planned-meals">
        {meals.length ? meals.map(meal => (
          <div className="planned-meal" key={meal.id}>
            <div className="food-emoji">{meal.emoji}</div>
            <div className="meal-info">
              <span className="meal-type">{meal.mealType}</span>
              <strong>{meal.foodName}</strong>
              <small>{meal.quantity} × {meal.servingLabel} · {Math.round(meal.servingGrams * meal.quantity)} g</small>
            </div>
            <div className="meal-right">
              <strong>{Math.round(meal.calories)} kcal</strong>
              <span>Logged today</span>
            </div>
          </div>
        )) : <div className="planner-empty"><p>No foods logged today yet.</p><button className="primary-button" type="button" onClick={() => setActivePage("Daily Meal Tracker")}>Open daily tracker <ArrowUpRight size={15} /></button></div>}
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
          <p>Keep logging your food in the Daily Meal Tracker to see your personal nutrition summary.</p>
        </div>
      </div>
    </>
  );
}
