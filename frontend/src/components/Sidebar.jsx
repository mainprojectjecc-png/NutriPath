
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
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-icon"><Leaf size={26} /></div>
        <div>
          <h2>NutriPath</h2>
          <span>HEALTHIER EVERY DAY</span>
        </div>
      </div>

      <p className="side-label">MAIN MENU</p>

      <nav className="side-menu">
        {menu.map(({ name, icon: Icon }) => (
          <button
            key={name}
            className={`nav-item ${activePage === name ? "active" : ""}`}
            onClick={() => setActivePage(name)}
          >
            <Icon size={19} />
            <span>{name}</span>
          </button>
        ))}
      </nav>

      <div className="sidebar-bottom">
        <p className="side-label">PREFERENCES</p>
        <button className="nav-item" onClick={() => setActivePage("Weight Journey")}>
          <CircleUserRound size={19} />
          My profile
        </button>
        <button className="nav-item" onClick={onLogout}>
          <LogOut size={19} />
          Sign out
        </button>

        <div className="sidebar-tip">
          <Leaf size={23} />
          <h4>{user?.full_name ? `You’ve got this, ${user.full_name.split(" ")[0]}!` : "Small steps, big changes!"}</h4>
          <p>Your progress is personal. Keep taking it one day at a time.</p>
        </div>
      </div>
    </aside>
  );
}
