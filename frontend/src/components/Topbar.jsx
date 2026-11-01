
import { Search, Bell, ChevronDown } from "lucide-react";

export default function Topbar() {
  return (
    <header className="topbar">
      <div className="top-search">
        <Search size={18} />
        <input placeholder="Search meals, goals, tips..." />
      </div>

      <div className="top-actions">
        <button className="icon-button" aria-label="Notifications"
          onClick={() => alert("You are all caught up!")}>
          <Bell size={20} />
          <span className="notification-dot"></span>
        </button>

        <div className="profile">
          <div className="avatar">N</div>
          <div className="profile-info">
            <strong>My Account</strong>
            <span>Healthy Explorer</span>
          </div>
          <ChevronDown size={17} />
        </div>
      </div>
    </header>
  );
}
