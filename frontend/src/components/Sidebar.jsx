
import {
  LayoutDashboard,
  Utensils,
  ClipboardList,
  TrendingUp,
  HeartPulse,
  Leaf,
  CircleUserRound,
  LogOut
} from "lucide-react";

const menu = [
  { name: "Dashboard", icon: LayoutDashboard },
  { name: "Daily Meal Tracker", icon: ClipboardList },
  { name: "Meal Planner", icon: Utensils },
  { name: "Weight Journey", icon: TrendingUp },
  { name: "Health Coach", icon: HeartPulse }
];

export default function Sidebar({ activePage, setActivePage, onLogout, user }) {
  const firstName = user?.full_name?.trim().split(/\s+/)[0];

  return (
    <aside className="sidebar" aria-label="Main sidebar">
      <div className="brand">
        <div className="brand-icon"><Leaf size={23} strokeWidth={2.2} /></div>
        <div>
          <h2>NutriPath</h2>
          <span>FOOD · FITNESS · WELLBEING</span>
        </div>
      </div>

      <p className="side-label">YOUR ROUTINE</p>

      <nav className="side-menu" aria-label="Main navigation">
        {menu.map(({ name, icon: Icon }) => (
          <button
            key={name}
            className={`nav-item ${activePage === name ? "active" : ""}`}
            aria-current={activePage === name ? "page" : undefined}
            onClick={() => setActivePage(name)}
          >
            <Icon size={18} strokeWidth={activePage === name ? 2.2 : 1.8} />
            <span>{name}</span>
          </button>
        ))}
      </nav>

      <div className="sidebar-bottom">
        <p className="side-label">ACCOUNT</p>
        <button className="nav-item" onClick={() => setActivePage("Weight Journey")}>
          <CircleUserRound size={19} />
          My progress
        </button>
        <button className="nav-item" onClick={onLogout}>
          <LogOut size={19} />
          Sign out
        </button>

        <div className="sidebar-tip">
          <span className="sidebar-tip-icon"><Leaf size={16} /></span>
          <span className="sidebar-tip-label">A NOTE FOR TODAY</span>
          <h4>{firstName ? `You’ve got this, ${firstName}.` : "Small steps. Strong habits."}</h4>
          <p>Progress comes from showing up, not from being perfect.</p>
        </div>
      </div>
    </aside>
  );
}
