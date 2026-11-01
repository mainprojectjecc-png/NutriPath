
import { useState } from "react";
import { Target, TrendingDown, Scale, CalendarDays } from "lucide-react";

const initialHistory = [
  { month: "Jun", weight: 72 },
  { month: "Jul", weight: 70 },
  { month: "Aug", weight: 69 },
  { month: "Sep", weight: 67 },
  { month: "Oct", weight: 66 },
  { month: "Nov", weight: 65.4 }
];

export default function WeightJourney() {
  const [history, setHistory] = useState(initialHistory);
  const [weight, setWeight] = useState("65.4");
  const [goal, setGoal] = useState("60");
  const [height, setHeight] = useState("1.65");
  const [message, setMessage] = useState("");

  const current = Number(weight);
  const target = Number(goal);
  const heightMetres = Number(height);

  const bmi = current > 0 && heightMetres > 0
    ? (current / (heightMetres ** 2)).toFixed(1)
    : "--";

  const progress = current >= 0 && target > 0 && current > target
    ? Math.min(100, Math.max(0, ((72 - current) / (72 - target)) * 100))
    : current === target ? 100 : 0;

  function saveWeight(e) {
    e.preventDefault();

    if (
      !Number.isFinite(current) || current <= 0 ||
      !Number.isFinite(target) || target <= 0 ||
      !Number.isFinite(heightMetres) || heightMetres <= 0
    ) {
      setMessage("Please enter valid measurements.");
      return;
    }

    setHistory(prev => [
      ...prev,
      { month: "New", weight: current }
    ]);

    setMessage("Weight entry added successfully (demo).");
  }

  return (
    <>
      <div className="page-title-row">
        <div>
          <span className="eyebrow">YOUR PERSONAL PROGRESS</span>
          <h1>Weight Journey</h1>
          <p>Track your progress and stay focused on your goals.</p>
        </div>
        <span className="today-label">
          <CalendarDays size={15} /> Progress tracker
        </span>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-top">
            <div><p className="muted">Current weight</p><h2>{current} <small>kg</small></h2></div>
            <div className="stat-icon green"><Scale /></div>
          </div>
          <span className="stat-note">Latest entered value</span>
        </div>

        <div className="stat-card">
          <div className="stat-top">
            <div><p className="muted">Target weight</p><h2>{target} <small>kg</small></h2></div>
            <div className="stat-icon purple"><Target /></div>
          </div>
          <span className="stat-note">Your personal goal</span>
        </div>

        <div className="stat-card">
          <div className="stat-top">
            <div><p className="muted">Weight difference</p><h2>{Math.abs(current - target).toFixed(1)} <small>kg</small></h2></div>
            <div className="stat-icon orange"><TrendingDown /></div>
          </div>
          <span className="stat-note">Difference from target</span>
        </div>

        <div className="stat-card">
          <div className="stat-top">
            <div><p className="muted">BMI estimate</p><h2>{bmi}</h2></div>
            <div className="stat-icon blue"><Scale /></div>
          </div>
          <span className="stat-note">Based on entered height and weight</span>
        </div>
      </div>

      <div className="dashboard-grid">
        <section className="panel">
          <div className="panel-heading">
            <div><h3>Weight history</h3><p>Sample monthly entries (kg)</p></div>
          </div>

          <div className="weight-chart">
            {history.map((item, index) => (
              <div className="chart-column" key={`${item.month}-${index}`}>
                <strong>{item.weight}</strong>
                <div
                  className="chart-bar"
                  style={{ height: `${Math.max(12, item.weight * 2)}px` }}
                />
                <span>{item.month}</span>
              </div>
            ))}
          </div>
        </section>

        <section className="panel">
          <h3>Goal progress</h3>
          <p className="muted">Progress towards your target</p>
          <div className="goal-progress-number">{Math.round(progress)}%</div>
          <div className="progress-track large">
            <div className="progress-fill green" style={{ width: `${progress}%` }} />
          </div>
          <p className="goal-caption">
            {current > target
              ? `${(current - target).toFixed(1)} kg between current and target weight.`
              : current === target
                ? "You have reached your entered target!"
                : "Your entered weight is below your target."}
          </p>
        </section>
      </div>

      <section className="panel weight-entry">
        <h3>Update your weight</h3>
        <p className="muted">Enter your latest measurements.</p>

        <form className="weight-form" onSubmit={saveWeight}>
          <div>
            <label>Current weight (kg)</label>
            <input type="number" min="1" step="0.1"
              value={weight} onChange={e => setWeight(e.target.value)} />
          </div>
          <div>
            <label>Target weight (kg)</label>
            <input type="number" min="1" step="0.1"
              value={goal} onChange={e => setGoal(e.target.value)} />
          </div>
          <div>
            <label>Height (metres)</label>
            <input type="number" min="0.5" step="0.01"
              value={height} onChange={e => setHeight(e.target.value)} />
          </div>
          <button className="primary-button" type="submit">Save progress</button>
        </form>

        {message && <p className="form-message">{message}</p>}
        <p className="muted">BMI is a screening estimate, not a medical diagnosis. All measurements shown initially are sample data.</p>
      </section>
    </>
  );
}
