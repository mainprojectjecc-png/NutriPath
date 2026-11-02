import { useMemo } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

function dateKey(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export default function NutritionChart({ meals, calorieGoal, period, onPeriodChange }) {
  const chartDays = useMemo(() => {
    const today = new Date();
    let start;
    let count;
    if (period === "week") {
      const weekday = (today.getDay() + 6) % 7;
      start = new Date(today.getFullYear(), today.getMonth(), today.getDate() - weekday);
      count = 7;
    } else {
      start = new Date(today.getFullYear(), today.getMonth(), 1);
      count = new Date(today.getFullYear(), today.getMonth() + 1, 0).getDate();
    }

    const totals = new Map();
    meals.forEach(meal => totals.set(meal.date, (totals.get(meal.date) || 0) + meal.calories));
    return Array.from({ length: count }, (_, index) => {
      const date = new Date(start.getFullYear(), start.getMonth(), start.getDate() + index);
      return { date, key: dateKey(date), calories: totals.get(dateKey(date)) || 0 };
    });
  }, [meals, period]);
  const maxCalories = Math.max(calorieGoal, ...chartDays.map(day => day.calories), 1);

  return (
    <section className="tracker-panel tracker-chart-panel">
      <div className="tracker-panel-heading">
        <div><h2>Nutrition trends</h2><p>Your logged calories over time</p></div>
        <div className="tracker-segmented" aria-label="Chart period">
          <button type="button" className={period === "week" ? "active" : ""} onClick={() => onPeriodChange("week")}>Week</button>
          <button type="button" className={period === "month" ? "active" : ""} onClick={() => onPeriodChange("month")}>Month</button>
        </div>
      </div>
      <div className={`tracker-chart tracker-chart-${period}`} role="img" aria-label={`${period === "week" ? "Weekly" : "Monthly"} logged calorie totals`}>
        {chartDays.map(day => (
          <div className={`tracker-chart-column ${day.calories ? "has-data" : ""}`} key={day.key} title={`${day.date.toLocaleDateString(undefined, { month: "short", day: "numeric" })}: ${Math.round(day.calories)} kcal logged`}>
            <span className="tracker-chart-value">{day.calories ? Math.round(day.calories) : ""}</span>
            <div className="tracker-chart-track">
              <span className="tracker-goal-marker" style={{ bottom: `${Math.min(calorieGoal / maxCalories * 100, 100)}%` }} />
              <span className="tracker-chart-bar" style={{ height: `${day.calories ? Math.max(day.calories / maxCalories * 100, 3) : 0}%` }} />
            </div>
            <span className="tracker-chart-label">{period === "week" ? day.date.toLocaleDateString(undefined, { weekday: "short" }) : day.date.getDate()}</span>
          </div>
        ))}
      </div>
      <div className="tracker-chart-legend"><span><i /> Calories logged</span><span><i className="goal-legend" /> Daily goal</span></div>
    </section>
  );
}
