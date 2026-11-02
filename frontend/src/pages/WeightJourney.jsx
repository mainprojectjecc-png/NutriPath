
import { useEffect, useMemo, useState } from "react";
import { CalendarDays, Check, ChevronRight, Flag, Pencil, Plus, Scale, ShieldCheck, Target, TrendingDown, Trophy } from "lucide-react";
import api from "../services/api";

function WeightChart({ journey }) {
  const points = useMemo(() => {
    const records = [
      { weight_kg: journey.goal.starting_weight_kg, measured_on: journey.goal.start_date, id: "start" },
      ...journey.weight_history
    ].sort((a, b) => a.measured_on.localeCompare(b.measured_on) || (a.id === "start" ? -1 : b.id === "start" ? 1 : a.id - b.id));
    const min = Math.min(...records.map(point => point.weight_kg), journey.goal.target_weight_kg);
    const max = Math.max(...records.map(point => point.weight_kg), journey.goal.target_weight_kg);
    const padding = Math.max((max - min) * .18, 1);
    const low = min - padding;
    const range = max - min + padding * 2 || 1;
    const height = 220;
    const plotted = records.map((point, index) => ({
      ...point,
      x: records.length === 1 ? 360 : 32 + index / (records.length - 1) * 656,
      y: 22 + (max + padding - point.weight_kg) / range * (height - 50)
    }));
    return { plotted, height, targetY: 22 + (max + padding - journey.goal.target_weight_kg) / range * (height - 50), target: journey.goal.target_weight_kg, low, high: max + padding };
  }, [journey]);
  const path = points.plotted.map((point, index) => `${index ? "L" : "M"} ${point.x} ${point.y}`).join(" ");

  return <div className="journey-chart-wrap">
    <svg className="journey-weight-chart" viewBox="0 0 720 220" role="img" aria-label="Weight history chart showing recorded measurements and target weight">
      {[0, 1, 2, 3].map(line => <g key={line}><line x1="30" x2="710" y1={28 + line * 48} y2={28 + line * 48} stroke="#edf2ee" strokeDasharray="3 5" /><text x="0" y={32 + line * 48} fill="#89978e" fontSize="10">{(points.high - (points.high - points.low) * line / 3).toFixed(0)}</text></g>)}
      <line x1="30" x2="710" y1={points.targetY} y2={points.targetY} stroke="#e5a84c" strokeDasharray="5 5" />
      <text x="707" y={Math.max(14, points.targetY - 5)} textAnchor="end" fill="#bc8432" fontSize="10">Target {points.target} kg</text>
      {points.plotted.length > 1 && <path d={path} fill="none" stroke="#16845c" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />}
      {points.plotted.map((point, index) => <g key={point.id}><circle cx={point.x} cy={point.y} r={point.id === "start" ? 5 : 4} fill={point.id === "start" ? "#fff" : "#16845c"} stroke="#16845c" strokeWidth="2"><title>{point.id === "start" ? "Starting" : index === points.plotted.length - 1 ? "Current and recorded" : "Recorded"} weight: {point.weight_kg} kg on {point.measured_on}</title></circle>{index === 0 || index === points.plotted.length - 1 ? <text x={point.x} y={Math.min(points.height - 2, point.y + 19)} textAnchor={index === 0 ? "start" : "end"} fill="#73877a" fontSize="9">{point.id === "start" && points.plotted.length === 1 ? "Starting · current" : new Date(`${point.measured_on}T12:00:00`).toLocaleDateString(undefined, { month: "short", day: "numeric" })}</text> : null}{index === points.plotted.length - 1 && point.id !== "start" ? <text x={point.x} y={Math.max(14, point.y - 8)} textAnchor="end" fill="#16845c" fontSize="9">Current {point.weight_kg} kg</text> : null}</g>)}
    </svg>
    <div className="journey-chart-legend"><span><i /> Recorded weight</span><span><i className="journey-target-legend" /> Target</span></div>
  </div>;
}

function PersonalFields({ profile, user, onSaved }) {
  const [values, setValues] = useState({ full_name: user.full_name, ...profile });
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => setValues({ full_name: user.full_name, ...profile }), [user, profile]);

  async function submit(event) {
    event.preventDefault();
    setSaving(true);
    setMessage("");
    try {
      const updated = await api.put("/api/profile", {
        full_name: values.full_name,
        age: Number(values.age),
        height_cm: Number(values.height_cm),
        gender: values.gender || null,
        activity_level: values.activity_level,
        dietary_preference: values.dietary_preference,
        allergies: values.allergies || "",
        exercise_preferences: values.exercise_preferences || "",
        daily_routine: values.daily_routine || ""
      });
      onSaved(updated);
      setMessage("Personal details updated.");
    } catch (error) {
      setMessage(error.message || "Could not update your details.");
    } finally {
      setSaving(false);
    }
  }

  return <form className="journey-edit-form" onSubmit={submit}>
    <div className="journey-edit-form-heading"><div><h3>Personal information</h3><p>Update your details and lifestyle preferences.</p></div><button className="journey-save-button" type="submit" disabled={saving}>{saving ? "Saving…" : "Save details"}</button></div>
    <div className="journey-edit-grid">
      <label>Full name<input required minLength="2" maxLength="120" value={values.full_name || ""} onChange={event => setValues({ ...values, full_name: event.target.value })} /></label>
      <label>Age<input type="number" min="13" max="120" required value={values.age || ""} onChange={event => setValues({ ...values, age: event.target.value })} /></label>
      <label>Height (cm)<input type="number" min="100" max="250" step="0.1" required value={values.height_cm || ""} onChange={event => setValues({ ...values, height_cm: event.target.value })} /></label>
      <label>Gender<select value={values.gender || ""} onChange={event => setValues({ ...values, gender: event.target.value })}><option value="">Prefer not to say</option><option value="female">Female</option><option value="male">Male</option><option value="non_binary">Non-binary</option><option value="self_described">Prefer to self-describe</option></select></label>
      <label>Activity level<select value={values.activity_level || "light"} onChange={event => setValues({ ...values, activity_level: event.target.value })}><option value="sedentary">Sedentary</option><option value="light">Light</option><option value="moderate">Moderate</option><option value="active">Active</option><option value="very_active">Very active</option></select></label>
      <label>Dietary preference<input required maxLength="60" value={values.dietary_preference || ""} onChange={event => setValues({ ...values, dietary_preference: event.target.value })} /></label>
      <label className="journey-edit-field-full">Allergies and restrictions<textarea maxLength="1000" rows="2" value={values.allergies || ""} onChange={event => setValues({ ...values, allergies: event.target.value })} /></label>
      <label className="journey-edit-field-full">Exercise preferences<textarea maxLength="1000" rows="2" value={values.exercise_preferences || ""} onChange={event => setValues({ ...values, exercise_preferences: event.target.value })} /></label>
      <label className="journey-edit-field-full">Daily routine<textarea maxLength="1000" rows="2" value={values.daily_routine || ""} onChange={event => setValues({ ...values, daily_routine: event.target.value })} /></label>
    </div>
    {message && <p className="journey-form-message" role="status">{message}</p>}
  </form>;
}

function GoalFields({ goal, onSaved }) {
  const [values, setValues] = useState({ ...goal });
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => setValues({ ...goal }), [goal]);

  async function submit(event) {
    event.preventDefault();
    setSaving(true);
    setMessage("");
    try {
      const updated = await api.put("/api/goals", {
        goal_type: values.goal_type,
        starting_weight_kg: Number(values.starting_weight_kg),
        target_weight_kg: Number(values.target_weight_kg),
        duration_weeks: Number(values.duration_weeks),
        start_date: values.start_date
      });
      onSaved(updated);
      setMessage("Weight goal updated.");
    } catch (error) {
      setMessage(error.message || "Could not update your goal.");
    } finally {
      setSaving(false);
    }
  }

  return <form className="journey-edit-form" onSubmit={submit}>
    <div className="journey-edit-form-heading"><div><h3>Weight goal</h3><p>Changing your starting point or goal updates journey calculations.</p></div><button className="journey-save-button" type="submit" disabled={saving}>{saving ? "Saving…" : "Save goal"}</button></div>
    <div className="journey-edit-grid">
      <label>Goal type<select value={values.goal_type} onChange={event => setValues({ ...values, goal_type: event.target.value })}><option value="weight_loss">Weight loss</option><option value="maintenance">Maintenance</option><option value="weight_gain">Weight gain</option></select></label>
      <label>Starting weight (kg)<input type="number" min="20.1" max="500" step="0.1" required value={values.starting_weight_kg} onChange={event => setValues({ ...values, starting_weight_kg: event.target.value })} /></label>
      <label>Target weight (kg)<input type="number" min="20.1" max="500" step="0.1" required value={values.target_weight_kg} onChange={event => setValues({ ...values, target_weight_kg: event.target.value })} /></label>
      <label>Duration (weeks)<input type="number" min="1" max="260" required value={values.duration_weeks} onChange={event => setValues({ ...values, duration_weeks: event.target.value })} /></label>
      <label>Journey start date<input type="date" required max={new Date().toISOString().slice(0, 10)} value={values.start_date} onChange={event => setValues({ ...values, start_date: event.target.value })} /></label>
    </div>
    {message && <p className="journey-form-message" role="status">{message}</p>}
  </form>;
}

export default function WeightJourney({ onUserUpdate }) {
  const [journey, setJourney] = useState(null);
  const [loading, setLoading] = useState(true);
  const [pageError, setPageError] = useState("");
  const [weight, setWeight] = useState("");
  const [measurementDate, setMeasurementDate] = useState(new Date().toISOString().slice(0, 10));
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const [entryMessage, setEntryMessage] = useState("");
  const [editOpen, setEditOpen] = useState(false);

  async function refresh() {
    setLoading(true);
    setPageError("");
    try {
      const data = await api.get("/api/journey");
      if (!data) throw new Error("Complete onboarding to view your journey.");
      setJourney(data);
    } catch (error) {
      setPageError(error.message || "Your journey could not be loaded.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { refresh(); }, []);

  async function addMeasurement(event) {
    event.preventDefault();
    const parsed = Number(weight);
    if (!Number.isFinite(parsed) || parsed <= 20 || parsed > 500) {
      setEntryMessage("Enter a weight between 20 and 500 kg.");
      return;
    }
    setSaving(true);
    setEntryMessage("");
    try {
      await api.post("/api/weight-entries", { weight_kg: parsed, measured_on: measurementDate, notes: notes.trim() });
      setWeight("");
      setNotes("");
      setEntryMessage("Measurement saved to your history.");
      await refresh();
    } catch (error) {
      setEntryMessage(error.message || "Your measurement could not be saved.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <div className="tracker-loading" role="status">Loading your weight journey…</div>;
  if (!journey) return <section className="journey-load-error" role="alert"><h2>Journey unavailable</h2><p>{pageError}</p><button className="journey-primary-button" type="button" onClick={refresh}>Try again</button></section>;

  const goal = journey.goal;
  const profile = journey.profile;
  const goalProgress = goal.journey_progress_percent;
  const achievements = journey.achievements || [];
  const statusLabel = goal.status === "goal_reached" ? "Goal reached" : goal.status === "target_date_passed" ? "Target date passed" : "In progress";

  return <div className="journey-page">
    <div className="journey-page-heading"><div><span className="tracker-eyebrow">YOUR PERSONAL PROGRESS</span><h1>My Weight Journey</h1><p>A steady path shaped around your goal and your real progress.</p></div><button className="journey-secondary-button journey-heading-edit" type="button" onClick={() => setEditOpen(value => !value)}><Pencil size={15} /> {editOpen ? "Close editor" : "Edit profile & goals"}</button></div>
    {pageError && <p className="journey-inline-error" role="alert">{pageError}</p>}
    {goal.unsafe_target && <div className="journey-safety-banner"><ShieldCheck size={19} /><div><strong>Review your target timeline</strong><p>{goal.safety_message}</p></div></div>}

    <section className="journey-profile-hero">
      <div className="journey-profile-welcome"><div className="journey-profile-avatar">{journey.user.full_name.trim().charAt(0).toUpperCase()}</div><div><span>YOUR JOURNEY PROFILE</span><h2>{journey.user.full_name}</h2><p>{profile.age} years · {profile.height_cm} cm · {profile.dietary_preference}</p></div></div>
      <span className={`journey-status journey-status-${goal.status}`}><i />{statusLabel}</span>
      <div className="journey-profile-goal"><div><small>STARTING WEIGHT</small><strong>{goal.starting_weight_kg} <span>kg</span></strong></div><ChevronRight size={17} /><div><small>CURRENT WEIGHT</small><strong>{goal.current_weight_kg} <span>kg</span></strong></div><ChevronRight size={17} /><div><small>TARGET WEIGHT</small><strong>{goal.target_weight_kg} <span>kg</span></strong></div></div>
      <div className="journey-profile-progress"><div><span>Journey progress</span><strong>{goalProgress}%</strong></div><div className="journey-profile-progress-track"><i style={{ width: `${goalProgress}%` }} /></div><small>{goal.remaining_weight_kg} kg remaining · {goal.total_weight_difference_kg} kg total goal</small></div>
    </section>

    <div className="journey-stat-grid">
      <article><span className="journey-stat-icon"><TrendingDown size={18} /></span><small>Total weight change</small><strong>{goal.total_weight_difference_kg} <em>kg</em></strong><p>{goal.goal_type.replace("_", " ")}</p></article>
      <article><span className="journey-stat-icon blue"><Scale size={18} /></span><small>Current BMI</small><strong>{goal.current_bmi ?? "Not shown"}</strong><p>{goal.current_bmi == null ? "Under 18: adult BMI not applicable" : "Screening indicator only"}</p></article>
      <article><span className="journey-stat-icon gold"><Target size={18} /></span><small>Weekly goal pace</small><strong>{goal.weekly_change_required_kg} <em>kg</em></strong><p>Estimated, not guaranteed</p></article>
      <article><span className="journey-stat-icon purple"><CalendarDays size={18} /></span><small>Estimated target</small><strong className="journey-stat-date">{new Date(`${goal.target_date}T12:00:00`).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })}</strong><p>Journey began {new Date(`${goal.start_date}T12:00:00`).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })}</p></article>
    </div>

    <div className="journey-content-grid">
      <section className="journey-content-panel"><div className="journey-content-heading"><div><h2>Weight history</h2><p>Every measurement is saved as a separate entry.</p></div><span>{journey.weight_history.length} {journey.weight_history.length === 1 ? "entry" : "entries"}</span></div><WeightChart journey={journey} />
        {journey.weight_history.length ? <div className="journey-history-list">{[...journey.weight_history].reverse().map(entry => <div className="journey-history-row" key={entry.id}><span className="journey-history-marker" /><div><strong>{entry.weight_kg} kg</strong><small>{new Date(`${entry.measured_on}T12:00:00`).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })}{entry.notes ? ` · ${entry.notes}` : ""}</small></div><span>{new Date(`${entry.measured_on}T12:00:00`).toLocaleDateString(undefined, { weekday: "short" })}</span></div>)}</div> : <p className="journey-no-history">No measurements yet. Your starting weight is shown on the chart.</p>}
      </section>
      <section className="journey-content-panel journey-entry-panel"><div className="journey-content-heading"><div><h2>Log a measurement</h2><p>Add a new weight to your history.</p></div><span className="journey-entry-icon"><Plus size={18} /></span></div>
        <form className="journey-weight-form" onSubmit={addMeasurement}><label>Weight (kg)<input type="number" min="20.1" max="500" step="0.1" value={weight} onChange={event => setWeight(event.target.value)} placeholder="e.g. 72.4" required /></label><label>Measurement date<input type="date" max={new Date().toISOString().slice(0, 10)} value={measurementDate} onChange={event => setMeasurementDate(event.target.value)} required /></label><label>Notes <span>Optional</span><textarea rows="3" maxLength="1000" value={notes} onChange={event => setNotes(event.target.value)} placeholder="Optional context for this measurement" /></label><button className="journey-primary-button" type="submit" disabled={saving}>{saving ? "Saving…" : "Save measurement"} {!saving && <Check size={16} />}</button></form>
        {entryMessage && <p className="journey-form-message" role="status">{entryMessage}</p>}
        <p className="journey-entry-note"><ShieldCheck size={14} /> Your measurements are private to your account.</p>
      </section>
    </div>

    <section className="journey-achievements-panel"><div className="journey-content-heading"><div><h2>Milestones & achievements</h2><p>Earned from your recorded progress.</p></div><Trophy size={20} color="#c9953f" /></div><div className="journey-achievement-grid">{achievements.map(item => <article key={item.code}><span><Flag size={16} /></span><div><strong>{item.title}</strong><p>{item.description}</p><small>{new Date(`${item.achieved_at.replace("Z", "")}Z`).toLocaleDateString()}</small></div></article>)}{achievements.length === 0 && <p className="journey-no-history">Your first milestone will appear here as your recorded progress grows.</p>}</div></section>

    <section className="journey-safety-note"><ShieldCheck size={17} /><p>BMI is a screening indicator, not a diagnosis. Weight changes can be affected by many factors. Your target date is an estimate, not a promise; consider discussing health goals with a qualified professional.</p></section>

    {editOpen && <div className="journey-edit-overlay" role="dialog" aria-modal="true" aria-label="Edit profile and goals"><div className="journey-edit-dialog"><div className="journey-edit-dialog-heading"><div><span className="tracker-eyebrow">YOUR JOURNEY</span><h2>Edit profile & goals</h2></div><button type="button" aria-label="Close editor" onClick={() => setEditOpen(false)}>×</button></div><PersonalFields profile={profile} user={journey.user} onSaved={updated => { setJourney(current => ({ ...current, ...updated })); onUserUpdate?.(updated.user); }} /><GoalFields goal={goal} onSaved={updated => setJourney(current => ({ ...current, ...updated }))} /></div></div>}
  </div>;
}
