
import { Activity } from "lucide-react";

export default function Topbar({ user, activePage }) {
  const accountType = typeof user?.role === "string" && user.role.trim()
    ? `${user.role.charAt(0).toUpperCase()}${user.role.slice(1)}`
    : "Wellness member";

  return (
    <header className="topbar">
      <div className="topbar-context">
        <span className="topbar-context-icon"><Activity size={17} /></span>
        <div>
          <span className="topbar-kicker">YOUR WELLNESS SPACE</span>
          <strong>{activePage}</strong>
        </div>
      </div>

      <div className="top-actions">
        <div className="profile" aria-label="Signed-in account">
          <div className="avatar">{user?.full_name?.trim().charAt(0).toUpperCase() || "N"}</div>
          <div className="profile-info">
            <strong>{user?.full_name || "My Account"}</strong>
            <span>{accountType}</span>
          </div>
        </div>
      </div>
    </header>
  );
}
