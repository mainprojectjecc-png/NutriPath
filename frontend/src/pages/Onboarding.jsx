import { useState } from "react";
import { ArrowLeft, ArrowRight, Check, Leaf, ShieldCheck } from "lucide-react";
import api from "../services/api";

const steps = ["Personal details", "Weight goals", "Your lifestyle", "Review"];
const initialForm = {
  full_name: "",
  age: "",
  height_cm: "",
  gender: "",
  starting_weight_kg: "",
  target_weight_kg: "",
  goal_type: "weight_loss",
  duration: "12",
  duration_unit: "weeks",
  start_date: new Date().toISOString().slice(0, 10),
  activity_level: "light",
  dietary_preference: "No preference",
  allergies: "",
  exercise_preferences: "",
  daily_routine: ""
};

function durationInWeeks(form) {
  const duration = Number(form.duration);
  return form.duration_unit === "months" ? Math.round(duration * 4.345) : duration;
}

function validateStep(step, form) {
  if (step === 0) {
    if (form.full_name.trim().length < 2) return "Enter your full name.";
    if (!Number.isFinite(Number(form.age)) || Number(form.age) < 13 || Number(form.age) > 120) return "Enter an age between 13 and 120.";
    if (!Number.isFinite(Number(form.height_cm)) || Number(form.height_cm) < 100 || Number(form.height_cm) > 250) return "Enter a height between 100 and 250 cm.";
  }
  if (step === 1) {
    const start = Number(form.starting_weight_kg);
    const target = Number(form.target_weight_kg);
    if (!Number.isFinite(start) || start <= 20 || start > 500) return "Enter a starting weight between 20 and 500 kg.";
    if (!Number.isFinite(target) || target <= 20 || target > 500) return "Enter a target weight between 20 and 500 kg.";
    if (form.goal_type === "weight_loss" && target >= start) return "For weight loss, your target must be below your starting weight.";
    if (form.goal_type === "weight_gain" && target <= start) return "For weight gain, your target must be above your starting weight.";
    if (form.goal_type === "maintenance" && Math.abs(start - target) > 2) return "A maintenance target should be within 2 kg of your starting weight.";
    const duration = Number(form.duration);
    if (!Number.isFinite(duration) || duration < 1 || duration > (form.duration_unit === "months" ? 59 : 260)) return "Choose a duration between 1 and 260 weeks (or 1 and 59 months).";
    if (!form.start_date || form.start_date > new Date().toISOString().slice(0, 10)) return "Choose a start date no later than today.";
  }
  if (step === 2 && form.dietary_preference.trim().length < 2) return "Choose a dietary preference.";
  return "";
}

function GoalSummary({ form }) {
  const difference = Math.abs(Number(form.starting_weight_kg) - Number(form.target_weight_kg));
  const weeks = durationInWeeks(form);
  const weeklyRate = weeks ? difference / weeks : 0;
  const unsafe = form.goal_type === "weight_loss" && (weeklyRate > 0.9 || weeklyRate / Number(form.starting_weight_kg) * 100 > 1);
  const targetDate = form.start_date ? new Date(`${form.start_date}T12:00:00`) : new Date();
  targetDate.setDate(targetDate.getDate() + weeks * 7);
  return <div className="journey-onboarding-summary">
    <div><span>Total weight change</span><strong>{difference.toFixed(1)} kg</strong></div>
    <div><span>Average weekly change</span><strong>{weeklyRate.toFixed(2)} kg / week</strong></div>
    <div><span>Estimated target date</span><strong>{targetDate.toLocaleDateString(undefined, { month: "long", day: "numeric", year: "numeric" })}</strong></div>
    {unsafe && <p className="journey-safety-warning"><ShieldCheck size={17} /> This weight-loss timeline may be faster than generally recommended. Consider adjusting it or discussing your goal with a qualified health professional. No outcome is guaranteed.</p>}
    <p className="journey-onboarding-disclaimer">Weight goals are estimates, not medical advice. BMI is a screening indicator, not a diagnosis.</p>
  </div>;
}

export default function Onboarding({ user, onComplete, onLogout }) {
  const [step, setStep] = useState(0);
  const [form, setForm] = useState({ ...initialForm, full_name: user.full_name });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function update(field, value) {
    setForm(current => ({ ...current, [field]: value }));
    setError("");
  }

  function next() {
    const validation = validateStep(step, form);
    if (validation) {
      setError(validation);
      return;
    }
    setError("");
    setStep(current => Math.min(current + 1, 3));
  }

  async function submit() {
    const validation = validateStep(1, form) || validateStep(2, form);
    if (validation) {
      setError(validation);
      return;
    }
    setLoading(true);
    setError("");
    try {
      const response = await api.post("/api/onboarding", {
        full_name: form.full_name.trim(),
        age: Number(form.age),
        height_cm: Number(form.height_cm),
        gender: form.gender || null,
        activity_level: form.activity_level,
        dietary_preference: form.dietary_preference,
        allergies: form.allergies.trim(),
        exercise_preferences: form.exercise_preferences.trim(),
        daily_routine: form.daily_routine.trim(),
        goal: {
          goal_type: form.goal_type,
          starting_weight_kg: Number(form.starting_weight_kg),
          target_weight_kg: Number(form.target_weight_kg),
          duration_weeks: durationInWeeks(form),
          start_date: form.start_date
        }
      });
      onComplete(response);
    } catch (requestError) {
      setError(requestError.message || "Your profile could not be saved.");
    } finally {
      setLoading(false);
    }
  }

  return <main className="journey-onboarding-page">
    <header className="journey-onboarding-topbar"><div className="journey-auth-logo"><span><Leaf size={22} /></span><div><strong>NutriPath</strong><small>YOUR HEALTHIER EVERY DAY</small></div></div><button type="button" onClick={onLogout}>Sign out</button></header>
    <div className="journey-onboarding-wrap">
      <div className="journey-onboarding-intro"><span className="tracker-eyebrow">YOUR JOURNEY STARTS HERE</span><h1>Let’s make this personal.</h1><p>A few details help us shape a thoughtful plan around your goals and everyday life.</p></div>
      <div className="journey-stepper" aria-label={`Step ${step + 1} of ${steps.length}`}>
        {steps.map((label, index) => <div className={`journey-step ${index === step ? "active" : ""} ${index < step ? "complete" : ""}`} key={label}><span>{index < step ? <Check size={15} /> : index + 1}</span><small>{label}</small></div>)}
      </div>
      <section className="journey-onboarding-card">
        <div className="journey-onboarding-card-heading"><span>STEP {step + 1} OF 4</span><h2>{steps[step]}</h2><p>{step === 0 ? "Tell us a little about yourself." : step === 1 ? "Choose a goal that feels sustainable for you." : step === 2 ? "Help personalize your recommendations." : "Take a look before we create your profile."}</p></div>

        {step === 0 && <div className="journey-onboarding-fields">
          <label className="journey-onboarding-field journey-field-full">Full name<input value={form.full_name} onChange={event => update("full_name", event.target.value)} minLength="2" maxLength="120" autoComplete="name" required /></label>
          <label className="journey-onboarding-field">Age<input type="number" value={form.age} onChange={event => update("age", event.target.value)} min="13" max="120" placeholder="e.g. 30" required /></label>
          <label className="journey-onboarding-field">Height (cm)<input type="number" value={form.height_cm} onChange={event => update("height_cm", event.target.value)} min="100" max="250" step="0.1" placeholder="e.g. 168" required /></label>
          <label className="journey-onboarding-field journey-field-full">Gender <span className="journey-optional">Optional</span><select value={form.gender} onChange={event => update("gender", event.target.value)}><option value="">Prefer not to say</option><option value="female">Female</option><option value="male">Male</option><option value="non_binary">Non-binary</option><option value="self_described">Prefer to self-describe</option></select></label>
        </div>}

        {step === 1 && <div className="journey-onboarding-fields">
          <label className="journey-onboarding-field">Current weight (kg)<input type="number" value={form.starting_weight_kg} onChange={event => update("starting_weight_kg", event.target.value)} min="20" max="500" step="0.1" placeholder="e.g. 78" required /></label>
          <label className="journey-onboarding-field">Target weight (kg)<input type="number" value={form.target_weight_kg} onChange={event => update("target_weight_kg", event.target.value)} min="20" max="500" step="0.1" placeholder="e.g. 68" required /></label>
          <label className="journey-onboarding-field">Goal type<select value={form.goal_type} onChange={event => update("goal_type", event.target.value)}><option value="weight_loss">Weight loss</option><option value="maintenance">Weight maintenance</option><option value="weight_gain">Weight gain</option></select></label>
          <label className="journey-onboarding-field">Desired duration<div className="journey-duration-field"><input type="number" value={form.duration} onChange={event => update("duration", event.target.value)} min="1" max={form.duration_unit === "months" ? "59" : "260"} required /><select value={form.duration_unit} onChange={event => update("duration_unit", event.target.value)}><option value="weeks">weeks</option><option value="months">months</option></select></div></label>
          <label className="journey-onboarding-field journey-field-full">Journey start date<input type="date" value={form.start_date} max={new Date().toISOString().slice(0, 10)} onChange={event => update("start_date", event.target.value)} required /></label>
          {Number(form.starting_weight_kg) > 20 && Number(form.target_weight_kg) > 20 && Number(form.duration) > 0 && <div className="journey-onboarding-review-full"><GoalSummary form={form} /></div>}
        </div>}

        {step === 2 && <div className="journey-onboarding-fields">
          <label className="journey-onboarding-field journey-field-full">Activity level<select value={form.activity_level} onChange={event => update("activity_level", event.target.value)}><option value="sedentary">Mostly sitting / sedentary</option><option value="light">Light activity</option><option value="moderate">Moderately active</option><option value="active">Active most days</option><option value="very_active">Very active</option></select></label>
          <label className="journey-onboarding-field journey-field-full">Dietary preference<select value={form.dietary_preference} onChange={event => update("dietary_preference", event.target.value)}>{["No preference", "Vegetarian", "Vegan", "Pescatarian", "Eggetarian", "Omnivore", "Other"].map(choice => <option key={choice}>{choice}</option>)}</select></label>
          <label className="journey-onboarding-field journey-field-full">Food allergies or restrictions <span className="journey-optional">Optional</span><textarea rows="2" value={form.allergies} onChange={event => update("allergies", event.target.value)} maxLength="1000" placeholder="List any allergies or foods you avoid" /></label>
          <label className="journey-onboarding-field journey-field-full">Exercise preferences <span className="journey-optional">Optional</span><textarea rows="2" value={form.exercise_preferences} onChange={event => update("exercise_preferences", event.target.value)} maxLength="1000" placeholder="Activities you enjoy or would like to try" /></label>
          <label className="journey-onboarding-field journey-field-full">Daily routine <span className="journey-optional">Optional</span><textarea rows="2" value={form.daily_routine} onChange={event => update("daily_routine", event.target.value)} maxLength="1000" placeholder="Anything about your schedule we should consider" /></label>
        </div>}

        {step === 3 && <div className="journey-review-list">
          <section><div><h3>Personal details</h3></div><button type="button" onClick={() => setStep(0)}>Edit</button><p><strong>{form.full_name}</strong> · {form.age} years · {form.height_cm} cm{form.gender ? ` · ${form.gender.replace("_", " ")}` : ""}</p></section>
          <section><div><h3>Weight goal</h3></div><button type="button" onClick={() => setStep(1)}>Edit</button><p>{form.goal_type.replace("_", " ")} · {form.starting_weight_kg} kg → {form.target_weight_kg} kg · {form.duration} {form.duration_unit}</p><p>Journey starts {new Date(`${form.start_date}T12:00:00`).toLocaleDateString()}</p></section>
          <section><div><h3>Lifestyle</h3></div><button type="button" onClick={() => setStep(2)}>Edit</button><p>{form.activity_level.replace("_", " ")} · {form.dietary_preference}</p><p>{form.allergies || "No allergies or restrictions added."}</p><p>{form.exercise_preferences || "No exercise preferences added."}</p><p>{form.daily_routine || "No daily routine notes added."}</p></section>
          {Number(form.starting_weight_kg) > 20 && Number(form.target_weight_kg) > 20 && <GoalSummary form={form} />}
          <p className="journey-review-consent">Your details are stored securely and only used to personalize your NutriPath experience.</p>
        </div>}

        {error && <p className="journey-form-error" role="alert">{error}</p>}
        <div className="journey-onboarding-actions">
          {step > 0 ? <button className="journey-secondary-button" type="button" onClick={() => { setError(""); setStep(current => current - 1); }}><ArrowLeft size={16} /> Back</button> : <span />}
          {step < 3 ? <button className="journey-primary-button" type="button" onClick={next}>Continue <ArrowRight size={16} /></button> : <button className="journey-primary-button" type="button" disabled={loading} onClick={submit}>{loading ? "Creating your profile…" : "Create my journey"} {!loading && <ArrowRight size={16} />}</button>}
        </div>
      </section>
      <p className="journey-onboarding-footer"><ShieldCheck size={14} /> Your health data is private and protected.</p>
    </div>
  </main>;
}
