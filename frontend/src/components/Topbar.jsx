import { useEffect, useMemo, useRef, useState } from "react";
import { Activity, ArrowRight, ClipboardList, HeartPulse, Plus, Search, TrendingUp, Utensils } from "lucide-react";

const destinations = [
  {
    name: "Dashboard",
    description: "Your daily health overview",
    keywords: "home calories protein water today",
    icon: Activity
  },
  {
    name: "Daily Meal Tracker",
    description: "Log meals and track nutrition",
    keywords: "food journal calories hydration water breakfast lunch dinner",
    icon: ClipboardList
  },
  {
    name: "Meal Planner",
    description: "Explore and plan your meals",
    keywords: "recipes food plan breakfast lunch dinner",
    icon: Utensils
  },
  {
    name: "Weight Journey",
    description: "Review your progress and goals",
    keywords: "weight progress goal milestones profile",
    icon: TrendingUp
  },
  {
    name: "Health Coach",
    description: "Get support with food choices",
    keywords: "coach support replacement request advice",
    icon: HeartPulse
  }
];

export default function Topbar({ user, activePage, setActivePage, onQuickLogMeal }) {
  const [query, setQuery] = useState("");
  const [searchOpen, setSearchOpen] = useState(false);
  const [activeResult, setActiveResult] = useState(0);
  const searchRef = useRef(null);
  const searchAreaRef = useRef(null);

  const accountType = typeof user?.role === "string" && user.role.trim()
    ? `${user.role.charAt(0).toUpperCase()}${user.role.slice(1)}`
    : "Wellness member";

  const results = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    if (!normalizedQuery) return destinations;
    return destinations.filter(destination =>
      `${destination.name} ${destination.description} ${destination.keywords}`
        .toLowerCase()
        .includes(normalizedQuery)
    );
  }, [query]);

  useEffect(() => {
    function handleShortcut(event) {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setSearchOpen(true);
        searchRef.current?.focus();
      }

      if (event.key === "Escape") {
        setSearchOpen(false);
        searchRef.current?.blur();
      }
    }

    function handleOutsideClick(event) {
      if (!searchAreaRef.current?.contains(event.target)) {
        setSearchOpen(false);
      }
    }

    document.addEventListener("keydown", handleShortcut);
    document.addEventListener("pointerdown", handleOutsideClick);
    return () => {
      document.removeEventListener("keydown", handleShortcut);
      document.removeEventListener("pointerdown", handleOutsideClick);
    };
  }, []);

  function navigateTo(page) {
    setActivePage(page);
    setQuery("");
    setSearchOpen(false);
    searchRef.current?.blur();
  }

  function handleSearchKeyDown(event) {
    if (event.key === "ArrowDown" && results.length) {
      event.preventDefault();
      setActiveResult(index => (index + 1) % results.length);
    } else if (event.key === "ArrowUp" && results.length) {
      event.preventDefault();
      setActiveResult(index => (index - 1 + results.length) % results.length);
    } else if (event.key === "Enter" && results.length) {
      event.preventDefault();
      navigateTo(results[activeResult]?.name || results[0].name);
    }
  }

  return (
    <header className="topbar">
      <div className="topbar-context">
        <span className="topbar-context-icon"><Activity size={17} /></span>
        <div>
          <span className="topbar-kicker">YOUR WELLNESS SPACE</span>
          <strong>{activePage}</strong>
        </div>
      </div>

      <div className="topbar-actions">
        <div className="topbar-search-area" ref={searchAreaRef}>
          <label className={`topbar-search${searchOpen ? " is-open" : ""}`}>
            <Search size={17} aria-hidden="true" />
            <span className="sr-only">Search NutriPath pages</span>
            <input
              ref={searchRef}
              type="search"
              role="combobox"
              aria-label="Search NutriPath pages"
              aria-expanded={searchOpen}
              aria-controls="topbar-search-results"
              aria-autocomplete="list"
              aria-activedescendant={searchOpen && results[activeResult] ? `topbar-result-${results[activeResult].name.replaceAll(" ", "-")}` : undefined}
              placeholder="Find a page or feature..."
              value={query}
              onFocus={() => setSearchOpen(true)}
              onChange={event => {
                setQuery(event.target.value);
                setActiveResult(0);
                setSearchOpen(true);
              }}
              onKeyDown={handleSearchKeyDown}
            />
            <kbd>Ctrl K</kbd>
          </label>

          {searchOpen && (
            <div className="topbar-search-results" id="topbar-search-results" role="listbox" aria-label="Pages and features">
              <span className="topbar-results-label">
                {query.trim() ? "MATCHING PAGES" : "QUICK NAVIGATION"}
              </span>
              {results.length ? results.map((destination, index) => {
                const Icon = destination.icon;
                const selected = index === activeResult;
                return (
                  <button
                    className={`topbar-result${selected ? " is-active" : ""}`}
                    id={`topbar-result-${destination.name.replaceAll(" ", "-")}`}
                    key={destination.name}
                    type="button"
                    role="option"
                    aria-selected={selected}
                    onMouseEnter={() => setActiveResult(index)}
                    onClick={() => navigateTo(destination.name)}
                  >
                    <span className="topbar-result-icon"><Icon size={16} /></span>
                    <span className="topbar-result-copy">
                      <strong>{destination.name}</strong>
                      <small>{destination.description}</small>
                    </span>
                    <ArrowRight size={15} aria-hidden="true" />
                  </button>
                );
              }) : (
                <p className="topbar-search-empty">
                  No matching pages. Try “meals”, “progress” or “coach”.
                </p>
              )}
              <span className="topbar-search-hint">Use ↑ ↓ to browse · Enter to open · Esc to close</span>
            </div>
          )}
        </div>

        <button
          className="topbar-quick-action"
          type="button"
          aria-label="Log a meal"
          onClick={() => {
            if (onQuickLogMeal) {
              setQuery("");
              setSearchOpen(false);
              onQuickLogMeal();
            } else {
              navigateTo("Daily Meal Tracker");
            }
          }}
        >
          <Plus size={16} />
          <span>Log a meal</span>
        </button>

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
