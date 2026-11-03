
import { useEffect, useMemo, useState } from "react";
import { ArrowUpRight, CalendarDays, Check, Leaf, Save, Send } from "lucide-react";
import {
  getNutritionData,
  createFoodReplacementRequest,
} from "../services/nutrition";
import {
  generateDietPlan,
  getDietPlans,
  saveDietPlan,
  updateDietPlan,
} from "../services/dietPlans";

function todayKey() {
  const today = new Date();
  return `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;
}

export default function MealPlanner({ userId, setActivePage }) {
  const [trackerData, setTrackerData] = useState(null);
  const [foodId, setFoodId] = useState("");
  const [reason, setReason] = useState("");
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [savedPlans, setSavedPlans] = useState([]);
  const [generatedPlan, setGeneratedPlan] = useState(null);
  const [planName, setPlanName] = useState("");
  const [planStartDate, setPlanStartDate] = useState(todayKey());
  const [planDays, setPlanDays] = useState("7");
  const [planLoading, setPlanLoading] = useState(true);
  const [planSaving, setPlanSaving] = useState(false);
  const [expandedPlanId, setExpandedPlanId] = useState(null);
  const [planMessage, setPlanMessage] = useState("");

  useEffect(() => {
    let active = true;
    getNutritionData(userId)
      .then(data => { if (active) setTrackerData(data); })
      .catch(error =>
        { if (active) setMessage(error.message || "Your food journal could not be loaded."); }
      );
    getDietPlans()
      .then(plans => { if (active) setSavedPlans(plans); })
      .catch(error =>
        { if (active) setPlanMessage(error.message || "Saved meal plans could not be loaded."); }
      )
      .finally(() => { if (active) setPlanLoading(false); });
    return () => { active = false; };
  }, [userId]);

  const meals = useMemo(
    () =>
      trackerData?.meals.filter(
        meal => meal.date === todayKey()
      ) || [],
    [trackerData]
  );

  const total = meals.reduce(
    (sum, meal) => sum + Number(meal.calories || 0),
    0
  );

  async function submitRequest(e) {
    e.preventDefault();

    if (!foodId || !reason) {
      setMessage("Please select a food and a reason.");
      return;
    }

    try {
      setSubmitting(true);
      setMessage("");

      await createFoodReplacementRequest(Number(foodId), reason);

      setMessage(
        "Your food replacement request was submitted successfully."
      );

      setFoodId("");
      setReason("");
    } catch (error) {
      const detail = error.response?.data?.detail || error.message;
      setMessage(
        error.status === 409 || detail === "The operation conflicts with existing data."
          ? "An active replacement request already exists for this food."
          : detail || "Could not submit your request. Please try again."
      );
    } finally {
      setSubmitting(false);
    }
  }

  async function generatePlan(event) {
    event.preventDefault();
    setPlanSaving(true);
    setPlanMessage("");
    try {
      const generated = await generateDietPlan(planStartDate, Number(planDays));
      setGeneratedPlan(generated);
      setPlanName(generated.PlanName);
    } catch (error) {
      setPlanMessage(error.message || "A meal plan could not be generated.");
    } finally {
      setPlanSaving(false);
    }
  }

  async function saveGeneratedPlan() {
    if (!generatedPlan || !planName.trim()) {
      setPlanMessage("Enter a name for this meal plan.");
      return;
    }
    setPlanSaving(true);
    setPlanMessage("");
    try {
      const plan = await saveDietPlan({
        PlanName: planName.trim(),
        StartDate: generatedPlan.StartDate,
        EndDate: generatedPlan.EndDate,
        Meals: generatedPlan.Meals.map(meal => ({
          MealDate: meal.MealDate,
          MealType: meal.MealType,
          Notes: meal.Notes,
          Items: meal.Items.map(item => ({
            FoodID: item.FoodID,
            Quantity: item.Quantity,
            ServingUnit: item.ServingUnit,
          })),
        })),
      });
      setSavedPlans(current => [plan, ...current]);
      setGeneratedPlan(null);
      setPlanMessage("Meal plan saved to your account.");
    } catch (error) {
      setPlanMessage(error.message || "The meal plan could not be saved.");
    } finally {
      setPlanSaving(false);
    }
  }

  async function changePlanStatus(plan, status) {
    setPlanMessage("");
    try {
      const updated = await updateDietPlan(plan.PlanID, { Status: status });
      setSavedPlans(current => current.map(item => item.PlanID === updated.PlanID ? updated : item));
    } catch (error) {
      setPlanMessage(error.message || "The meal plan could not be updated.");
    }
  }

  return (
    <>
      <div className="page-title-row">
        <div>
          <span className="eyebrow">NUTRITION MANAGEMENT</span>
          <h1>Meal Planner</h1>
          <p>Plan balanced meals and make healthier food choices.</p>
        </div>

        <button
          className="primary-button"
          onClick={() => setActivePage("Daily Meal Tracker")}
        >
          <ArrowUpRight size={17} /> Log food
        </button>
      </div>

      <div className="meal-summary">
        <div>
          <span>Today's logged calories</span>
          <h2>{Math.round(total)} <small>kcal</small></h2>
          <p>
            Daily goal:{" "}
            {trackerData?.calorieGoal.toLocaleString() || "—"} kcal
          </p>
        </div>
        <div className="hero-art">🥑</div>
      </div>

      <div className="section-heading">
        <div>
          <h2>Build a meal plan</h2>
          <p>Meals are selected from active catalog foods and their saved nutrition values.</p>
        </div>
      </div>

      <form className="panel request-form" onSubmit={generatePlan}>
        <label htmlFor="plan-start-date">Plan start date</label>
        <input
          id="plan-start-date"
          type="date"
          value={planStartDate}
          onChange={event => setPlanStartDate(event.target.value)}
          required
        />
        <label htmlFor="plan-days">Plan length</label>
        <select id="plan-days" value={planDays} onChange={event => setPlanDays(event.target.value)}>
          {[1, 2, 3, 4, 5, 6, 7].map(days => <option key={days} value={days}>{days} {days === 1 ? "day" : "days"}</option>)}
        </select>
        <button className="primary-button" type="submit" disabled={planSaving}>
          <CalendarDays size={16} /> {planSaving ? "Generating…" : "Generate plan"}
        </button>
      </form>

      {planMessage && <p className="form-message" role="status">{planMessage}</p>}

      {generatedPlan && <section>
        <div className="section-heading">
          <div>
            <h2>Generated plan preview</h2>
            <p>{generatedPlan.GoalType.replace("_", " ")} · {generatedPlan.DailyCalorieGoal.toLocaleString()} kcal/day · Review before saving.</p>
          </div>
        </div>
        <div className="panel request-form">
          <label htmlFor="generated-plan-name">Plan name</label>
          <input id="generated-plan-name" maxLength="100" value={planName} onChange={event => setPlanName(event.target.value)} />
          <p>{generatedPlan.Notice}</p>
          <button className="primary-button" type="button" disabled={planSaving} onClick={saveGeneratedPlan}>
            <Save size={16} /> {planSaving ? "Saving…" : "Save meal plan"}
          </button>
        </div>
        <div className="planned-meals">
          {generatedPlan.Meals.map(meal => meal.Items.map(item => (
            <div className="planned-meal" key={`${meal.MealDate}-${meal.MealType}-${item.FoodID}`}>
              <div className="food-emoji"><CalendarDays size={17} /></div>
              <div className="meal-info">
                <span className="meal-type">{meal.MealType} · {new Date(`${meal.MealDate}T12:00:00`).toLocaleDateString(undefined, { month: "short", day: "numeric" })}</span>
                <strong>{item.Food.FoodName}</strong>
                <small>{Number(item.Quantity)} × {item.ServingUnit} · P {Number(item.Food.Protein * item.Quantity).toFixed(1)}g · C {Number(item.Food.Carbs * item.Quantity).toFixed(1)}g · F {Number(item.Food.Fat * item.Quantity).toFixed(1)}g</small>
              </div>
              <div className="meal-right">
                <strong>{Math.round(Number(item.Food.Calories) * Number(item.Quantity))} kcal</strong>
                <span>Catalog estimate</span>
              </div>
            </div>
          )))}
        </div>
      </section>}

      <div className="section-heading">
        <div>
          <h2>Saved meal plans</h2>
          <p>Plans are stored with meals linked to valid food catalog records.</p>
        </div>
      </div>
      {planLoading ? <p role="status">Loading saved plans…</p> : savedPlans.length ? (
        <div className="planned-meals">
          {savedPlans.map(plan => <div className="planned-meal" key={plan.PlanID}>
            <div className="food-emoji"><Check size={17} /></div>
            <div className="meal-info">
              <strong>{plan.PlanName}</strong>
              <small>{plan.StartDate} – {plan.EndDate} · {plan.Meals.length} planned meals · {plan.Status}</small>
              <button className="small-button" type="button" onClick={() => setExpandedPlanId(expandedPlanId === plan.PlanID ? null : plan.PlanID)}>
                {expandedPlanId === plan.PlanID ? "Hide meals" : "View meals"}
              </button>
            </div>
            <div className="meal-right">
              {plan.Status === "Active" ? <>
                <button className="small-button" type="button" onClick={() => changePlanStatus(plan, "Paused")}>Pause</button>
                <button className="small-button" type="button" onClick={() => changePlanStatus(plan, "Completed")}>Complete</button>
              </> : <button className="small-button" type="button" onClick={() => changePlanStatus(plan, "Active")}>Resume</button>}
            </div>
            {expandedPlanId === plan.PlanID && <div className="meal-info">
              {plan.Meals.map(meal => meal.Items.map(item => (
                <small key={item.MealItemID}>{meal.MealDate} · {meal.MealType}: {item.Food.FoodName} ({item.Quantity} {item.ServingUnit}; P {Number(item.Food.Protein * item.Quantity).toFixed(1)}g · C {Number(item.Food.Carbs * item.Quantity).toFixed(1)}g · F {Number(item.Food.Fat * item.Quantity).toFixed(1)}g)</small>
              )))}
            </div>}
          </div>)}
        </div>
      ) : <div className="planner-empty"><p>No saved meal plans yet.</p></div>}

      <div className="section-heading">
        <div>
          <h2>Meals logged today</h2>
          <p>Based on foods in your daily tracker.</p>
        </div>
      </div>

      <div className="planned-meals">
        {meals.length ? (
          meals.map(meal => (
            <div className="planned-meal" key={meal.id}>
              <div className="food-emoji">{meal.emoji}</div>

              <div className="meal-info">
                <span className="meal-type">{meal.mealType}</span>
                <strong>{meal.foodName}</strong>
                <small>
                  {meal.quantity} × {meal.servingLabel} ·{" "}
                  {Math.round(
                    meal.servingGrams * meal.quantity
                  )} g
                </small>
              </div>

              <div className="meal-right">
                <strong>
                  {Math.round(meal.calories)} kcal
                </strong>
                <span>Logged today</span>
              </div>
            </div>
          ))
        ) : (
          <div className="planner-empty">
            <p>No foods logged today yet.</p>
            <button
              className="primary-button"
              type="button"
              onClick={() =>
                setActivePage("Daily Meal Tracker")
              }
            >
              Open daily tracker <ArrowUpRight size={15} />
            </button>
          </div>
        )}
      </div>

      <div className="section-heading">
        <div>
          <h2>Food replacement request</h2>
          <p>
            Request alternatives for foods that don't suit
            your preferences.
          </p>
        </div>
      </div>

      <form
        className="panel request-form"
        onSubmit={submitRequest}
      >
        <label htmlFor="replacement-food">
          Food you want to replace
        </label>

        <select
          id="replacement-food"
          value={foodId}
          onChange={e => setFoodId(e.target.value)}
          required
        >
          <option value="">Select a logged food</option>
          {meals.map(meal => (
            <option key={meal.id} value={meal.id}>
              {meal.foodName} ({meal.mealType})
            </option>
          ))}
        </select>

        <label htmlFor="replacement-reason">
          Reason for replacement
        </label>

        <select
          id="replacement-reason"
          value={reason}
          onChange={e => setReason(e.target.value)}
          required
        >
          <option value="">Select a reason</option>
          <option value="Food preference">
            Food preference
          </option>
          <option value="Allergy or intolerance">
            Allergy or intolerance
          </option>
          <option value="Not available">
            Not available
          </option>
          <option value="Other">Other</option>
        </select>

        <button
          className="primary-button"
          type="submit"
          disabled={submitting || meals.length === 0}
        >
          <Send size={16} />
          {submitting ? "Submitting..." : "Submit request"}
        </button>

        {message && (
          <p className="form-message" role="status">
            {message}
          </p>
        )}
      </form>

      <div className="recommendation">
        <Leaf size={24} />
        <div>
          <strong>Healthy eating reminder</strong>
          <p>
            Keep logging your food in the Daily Meal Tracker
            to see your personal nutrition summary.
          </p>
        </div>
      </div>
    </>
  );
}
