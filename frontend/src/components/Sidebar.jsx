
import {
  LayoutDashboard,
  Utensils,
  TrendingUp,
  HeartPulse,
  Leaf,
  Settings,
  LogOut
} from "lucide-react";

const menu = [
  { name: "Dashboard", icon: LayoutDashboard },
  { name: "Meal Planner", icon: Utensils },
  { name: "Weight Journey", icon: TrendingUp },
  { name: "Health Coach", icon: HeartPulse }
];

export default function Sidebar({ activePage, setActivePage }) {
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
        <button className="nav-item" onClick={() => alert("Settings coming soon")}>
          <Settings size={19} />
          Settings
        </button>
        <button className="nav-item" onClick={() => setActivePage("Dashboard")}>
          <LogOut size={19} />
          Logout
        </button>

        <div className="sidebar-tip">
          <Leaf size={23} />
          <h4>Small steps, big changes!</h4>
          <p>Every healthy choice brings you closer to your goals.</p>
        </div>
      </div>
    </aside>
  );
}
