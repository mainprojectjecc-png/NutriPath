import { useEffect, useMemo, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

function keyForDate(date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

export default function MealHistoryCalendar({ meals, selectedDate, onSelectDate }) {
  const [viewedMonth, setViewedMonth] = useState(() => new Date(`${selectedDate}T12:00:00`));
  const days = useMemo(() => {
    const year = viewedMonth.getFullYear();
    const month = viewedMonth.getMonth();
    const firstWeekday = (new Date(year, month, 1).getDay() + 6) % 7;
    const dayCount = new Date(year, month + 1, 0).getDate();
    return [
      ...Array(firstWeekday).fill(null),
      ...Array.from({ length: dayCount }, (_, index) => new Date(year, month, index + 1))
    ];
  }, [viewedMonth]);
  const loggedDays = useMemo(() => new Set(meals.map(meal => meal.date)), [meals]);

  useEffect(() => {
    setViewedMonth(new Date(`${selectedDate}T12:00:00`));
  }, [selectedDate]);

  function changeMonth(amount) {
    setViewedMonth(current => new Date(current.getFullYear(), current.getMonth() + amount, 1));
  }

  return (
    <section className="tracker-panel tracker-calendar-panel">
      <div className="tracker-panel-heading">
        <div><h2>Meal history</h2><p>Choose a day to review or add meals</p></div>
      </div>
      <div className="tracker-calendar-month">
        <strong>{viewedMonth.toLocaleDateString(undefined, { month: "long", year: "numeric" })}</strong>
        <div><button type="button" className="tracker-icon-button" aria-label="Previous month" onClick={() => changeMonth(-1)}><ChevronLeft size={17} /></button><button type="button" className="tracker-icon-button" aria-label="Next month" onClick={() => changeMonth(1)}><ChevronRight size={17} /></button></div>
      </div>
      <div className="tracker-calendar-grid">
        {["M", "T", "W", "T", "F", "S", "S"].map((day, index) => <span className="tracker-calendar-weekday" key={`${day}-${index}`}>{day}</span>)}
        {days.map((day, index) => day ? (
          <button type="button" className={`tracker-calendar-day ${keyForDate(day) === selectedDate ? "selected" : ""} ${loggedDays.has(keyForDate(day)) ? "logged" : ""}`} key={keyForDate(day)} aria-label={`${day.toLocaleDateString()}${loggedDays.has(keyForDate(day)) ? ", meals logged" : ""}`} onClick={() => onSelectDate(keyForDate(day))}>
            {day.getDate()}{loggedDays.has(keyForDate(day)) && <i />}
          </button>
        ) : <span className="tracker-calendar-empty" key={`empty-${index}`} />)}
      </div>
      <p className="tracker-calendar-legend"><i /> Days with logged meals</p>
    </section>
  );
}
