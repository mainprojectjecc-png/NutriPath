
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";

export default function Layout({
  activePage,
  setActivePage,
  children
}) {
  return (
    <div className="app-layout">
      <Sidebar
        activePage={activePage}
        setActivePage={setActivePage}
      />

      <main className="main-area">
        <Topbar />
        <div className="page-content">
          {children}
          <footer className="footer">
            <span>© 2026 NutriPath. All rights reserved.</span>
            <span>Better Choices · Healthier You ♥</span>
          </footer>
        </div>
      </main>
    </div>
  );
}
