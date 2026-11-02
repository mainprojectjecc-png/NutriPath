import { useMemo, useState } from "react";
import { Search, X } from "lucide-react";
import { foodCatalog } from "./foodCatalog";

function getServingOptions(food) {
  return [
    { label: food.servingLabel, grams: food.servingGrams },
    { label: `${food.servingGrams} g`, grams: food.servingGrams },
    { label: `${Math.round(food.servingGrams * 1.5)} g`, grams: food.servingGrams * 1.5 },
    { label: `${food.servingGrams * 2} g`, grams: food.servingGrams * 2 }
  ].filter((option, index, options) => options.findIndex(item => item.label === option.label) === index);
}

export default function MealFoodModal({ mealType, onClose, onAdd }) {
  const [query, setQuery] = useState("");
  const [selectedFood, setSelectedFood] = useState(null);
  const [servingLabel, setServingLabel] = useState("");
  const [quantity, setQuantity] = useState("1");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const filteredFoods = useMemo(() => {
    const search = query.trim().toLocaleLowerCase();
    return foodCatalog.filter(food =>
      (!search || food.name.toLocaleLowerCase().includes(search)) &&
      (food.category === mealType || !search)
    );
  }, [mealType, query]);
  const servingOptions = selectedFood ? getServingOptions(selectedFood) : [];
  const selectedServing = servingOptions.find(option => option.label === servingLabel) || servingOptions[0];
  const servings = Number(quantity);
  const multiplier = selectedFood && selectedServing ? selectedServing.grams / selectedFood.servingGrams * servings : 0;
  const nutrients = selectedFood ? {
    calories: selectedFood.calories * multiplier,
    protein: selectedFood.protein * multiplier,
    carbs: selectedFood.carbs * multiplier,
    fats: selectedFood.fats * multiplier
  } : null;

  function chooseFood(food) {
    setSelectedFood(food);
    setServingLabel(food.servingLabel);
    setQuantity("1");
    setError("");
  }

  async function submit(event) {
    event.preventDefault();
    if (!selectedFood) {
      setError("Choose a food to add to your meal.");
      return;
    }
    if (!Number.isFinite(servings) || servings <= 0 || servings > 50) {
      setError("Enter a quantity greater than 0 and no more than 50.");
      return;
    }

    setSaving(true);
    setError("");
    try {
      await onAdd({
        foodId: selectedFood.id,
        foodName: selectedFood.name,
        emoji: selectedFood.emoji,
        mealType,
        quantity: servings,
        servingLabel: selectedServing.label,
        servingGrams: selectedServing.grams,
        ...Object.fromEntries(Object.entries(nutrients).map(([key, value]) => [key, Math.round(value * 10) / 10]))
      });
    } catch (requestError) {
      setError(requestError.message || "This food could not be saved.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="tracker-modal-backdrop" onMouseDown={event => event.target === event.currentTarget && onClose()}>
      <section className="tracker-food-modal" role="dialog" aria-modal="true" aria-labelledby="food-modal-title">
        <div className="tracker-modal-heading">
          <div>
            <span className="tracker-eyebrow">ADD TO {mealType.toUpperCase()}</span>
            <h2 id="food-modal-title">{selectedFood ? "Choose your serving" : "Find a food"}</h2>
          </div>
          <button type="button" className="tracker-icon-button" aria-label="Close food search" onClick={onClose} disabled={saving}><X size={19} /></button>
        </div>

        {!selectedFood ? (
          <>
            <label className="tracker-search-field">
              <Search size={18} />
              <input autoFocus value={query} onChange={event => setQuery(event.target.value)} placeholder="Search Indian foods..." aria-label="Search foods" />
            </label>
            <div className="tracker-food-results">
              {filteredFoods.length ? filteredFoods.map(food => (
                <button type="button" className="tracker-food-option" key={food.id} onClick={() => chooseFood(food)}>
                  <span className="tracker-food-emoji">{food.emoji}</span>
                  <span className="tracker-food-option-copy"><strong>{food.name}</strong><small>{food.servingLabel} · {food.calories} kcal</small></span>
                  <span className="tracker-food-option-meal">{food.category}</span>
                </button>
              )) : <p className="tracker-empty-state">No foods found. Try another search.</p>}
            </div>
          </>
        ) : (
          <form onSubmit={submit}>
            <button type="button" className="tracker-back-link" onClick={() => setSelectedFood(null)}>← Choose a different food</button>
            <div className="tracker-selected-food"><span>{selectedFood.emoji}</span><div><strong>{selectedFood.name}</strong><small>Nutrition values are estimates per serving</small></div></div>
            <div className="tracker-serving-fields">
              <label>Serving size
                <select value={selectedServing.label} onChange={event => setServingLabel(event.target.value)}>
                  {servingOptions.map(option => <option key={option.label} value={option.label}>{option.label}</option>)}
                </select>
              </label>
              <label>Quantity
                <input type="number" min="0.1" max="50" step="0.1" value={quantity} onChange={event => setQuantity(event.target.value)} inputMode="decimal" />
              </label>
            </div>
            <div className="tracker-modal-nutrition">
              <span><strong>{Math.round(nutrients.calories)}</strong> kcal</span>
              <span><strong>{nutrients.protein.toFixed(1)}g</strong> protein</span>
              <span><strong>{nutrients.carbs.toFixed(1)}g</strong> carbs</span>
              <span><strong>{nutrients.fats.toFixed(1)}g</strong> fats</span>
            </div>
            {error && <p className="tracker-form-error" role="alert">{error}</p>}
            <button className="tracker-primary-button tracker-modal-submit" type="submit" disabled={saving}>{saving ? "Saving…" : `Add to ${mealType}`}</button>
          </form>
        )}
      </section>
    </div>
  );
}
