import { useState } from "react";
import { Activity, ArrowRight, CalendarDays, Dumbbell, Leaf, Sparkles, Utensils } from "lucide-react";

const focuses = [
  {
    icon: Utensils,
    label: "Eat well",
    title: "Make nutrition easier to understand.",
    description: "Log your meals, explore the nutrients and make informed food choices that suit your day.",
    steps: ["Record meals", "Review daily nutrition", "Plan your next meal"]
  },
  {
    icon: Dumbbell,
    label: "Move more",
    title: "Build movement into your routine.",
    description: "Set a personal direction and make room for steady, achievable progress—one day at a time.",
    steps: ["Choose a personal goal", "Build a steady routine", "Reflect on your progress"]
  },
  {
    icon: Sparkles,
    label: "Feel your best",
    title: "Create habits that work for you.",
    description: "Bring food, movement and personal goals together in a supportive space that grows with you.",
    steps: ["Start with one small step", "Track what matters to you", "Celebrate consistency"]
  }
];

const wellnessSignals = [
  { icon: Utensils, label: "Nourish" },
  { icon: Dumbbell, label: "Move" },
  { icon: Sparkles, label: "Restore" }
];

export default function WelcomePage({ onGetStarted, onSignIn }) {
  const [selectedFocus, setSelectedFocus] = useState(0);
  const focus = focuses[selectedFocus];
  const FocusIcon = focus.icon;

  return (
    <main className="welcome-page">
      <header className="welcome-header">
        <a className="welcome-brand" href="/" aria-label="NutriPath home">
          <span><Leaf size={22} /></span>
          <strong>NutriPath</strong>
        </a>
        <button className="welcome-sign-in" type="button" onClick={onSignIn}>Sign in</button>
      </header>

      <section className="welcome-hero" aria-labelledby="welcome-heading">
        <div className="welcome-hero-copy">
          <span className="welcome-eyebrow">A THOUGHTFUL APPROACH TO EVERYDAY WELLBEING</span>
          <h1 id="welcome-heading">Wellbeing,<br /><span>shaped around you.</span></h1>
          <p>
            Make informed choices, build healthy routines and follow your
            progress with practical tools designed to fit your life.
          </p>
          <div className="welcome-focus-picker">
            <span className="welcome-focus-label">WHAT WOULD YOU LIKE TO FOCUS ON?</span>
            <div className="welcome-focus-options" role="group" aria-label="Choose your wellbeing focus">
              {focuses.map(({ icon: Icon, label }, index) => (
                <button
                  type="button"
                  className={`welcome-focus-option${selectedFocus === index ? " is-selected" : ""}`}
                  key={label}
                  aria-pressed={selectedFocus === index}
                  onClick={() => setSelectedFocus(index)}
                >
                  <Icon size={16} />{label}
                </button>
              ))}
            </div>
          </div>
          <div className="welcome-actions">
            <button className="welcome-primary-button" type="button" onClick={onGetStarted}>
              Create your account <ArrowRight size={17} />
            </button>
            <span>Small steps. Your pace.</span>
          </div>
        </div>

        <aside className="welcome-preview" data-focus={selectedFocus} aria-label="A preview of your NutriPath journey">
          <div className="welcome-preview-top">
            <span className="welcome-preview-brand"><Leaf size={15} /> NUTRIPATH</span>
            <span className="welcome-preview-tag">YOUR WELLNESS, YOUR WAY</span>
          </div>
          <div className="welcome-balance-visual" aria-label="A balanced approach: nourish, move, restore">
            <span className="welcome-balance-line" aria-hidden="true" />
            {wellnessSignals.map(({ icon: Icon, label }, index) => (
              <span className={`welcome-balance-signal${selectedFocus === index ? " is-active" : ""}`} key={label}>
                <i><Icon size={16} /></i>
                <small>{label}</small>
              </span>
            ))}
          </div>
          <div aria-live="polite" aria-atomic="true">
            <div className="welcome-preview-heading">
              <span className="welcome-preview-icon"><FocusIcon size={21} /></span>
              <div><span className="welcome-preview-kicker">A PERSONAL STARTING POINT</span><h2 key={focus.title}>{focus.title}</h2></div>
            </div>
            <p className="welcome-preview-description" key={focus.description}>{focus.description}</p>
          </div>
          <div className="welcome-preview-divider" />
          <span className="welcome-preview-kicker">SIMPLE STEPS, BUILT AROUND YOU</span>
          <ol className="welcome-preview-steps" key={focus.label}>
            {focus.steps.map((step, index) => (
              <li key={step}><span>{index + 1}</span>{step}<i /></li>
            ))}
          </ol>
          <div className="welcome-preview-foot"><Activity size={15} /> Practical tools. Your pace.</div>
        </aside>
      </section>

      <section className="welcome-pillars" aria-label="The NutriPath approach">
        <div className="welcome-pillars-heading">
          <span className="welcome-eyebrow">OUR PURPOSE</span>
          <h2>Healthy living should feel clear, personal and possible.</h2>
          <p>We turn your goals into practical next steps—with thoughtful tools for everyday nutrition, meal planning and progress.</p>
        </div>
        <div className="welcome-pillar-grid" aria-label="NutriPath tools">
          {[
            { icon: Utensils, title: "Nutrition that makes sense", description: "Understand your meals and make choices with confidence." },
            { icon: CalendarDays, title: "Plans for real life", description: "Organize balanced meals around your routine." },
            { icon: Activity, title: "Progress you can follow", description: "Keep track of your goals and recognize steady effort." }
          ].map(({ icon: Icon, title, description }) => (
            <article className="welcome-pillar" key={title}>
              <span><Icon size={19} /></span>
              <h3>{title}</h3>
              <p>{description}</p>
            </article>
          ))}
        </div>
      </section>
      <footer className="welcome-footer">NutriPath · A thoughtful companion for everyday wellbeing.</footer>
    </main>
  );
}
