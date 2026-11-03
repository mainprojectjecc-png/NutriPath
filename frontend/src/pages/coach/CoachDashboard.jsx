import { useEffect, useState } from "react";
import { getCoachRequests, sendSuggestion, respondToSuggestion } from "../../services/coachApi";
import RequestList from "../../components/coach/RequestList";
import SuggestionForm from "../../components/coach/SuggestionForm";
import RequestStatusBadge from "../../components/coach/RequestStatusBadge";

const FILTERS = ["all", "pending", "suggested", "accepted", "rejected"];

export default function CoachDashboard() {
  const [requests, setRequests] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [filter, setFilter] = useState("pending");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    getCoachRequests()
      .then(setRequests)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const selected = requests.find((r) => r.id === selectedId) || null;
  const visible = filter === "all" ? requests : requests.filter((r) => r.status === filter);
  const pendingCount = requests.filter((r) => r.status === "pending").length;

  const update = (updated) =>
    setRequests((prev) => prev.map((r) => (r.id === updated.id ? updated : r)));

  async function run(action, successMessage) {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const updated = await action();
      update(updated);
      setMessage(successMessage);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  const handleSuggest = (text) =>
    run(() => sendSuggestion(selected.id, text), "Suggestion sent");

  const handleRespond = (accepted) =>
    run(
      () => respondToSuggestion(selected.id, accepted),
      accepted ? "Request accepted" : "Request rejected"
    );

  if (loading) return <p>Loading requests...</p>;

  return (
    <div>
      <h2>Coach Dashboard</h2>
      <p>{pendingCount} pending request(s)</p>

      {message && <p style={{ color: "#16a34a" }}>{message}</p>}
      {error && <p style={{ color: "#dc2626" }}>{error}</p>}

      <div style={{ marginBottom: 12 }}>
        {FILTERS.map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            style={{ marginRight: 6, fontWeight: filter === f ? "bold" : "normal" }}
          >
            {f}
          </button>
        ))}
      </div>

      {visible.length === 0 ? (
        <p>No {filter} requests.</p>
      ) : (
        <RequestList requests={visible} onSelect={(r) => setSelectedId(r.id)} />
      )}

      {selected && (
        <div style={{ marginTop: 16, borderTop: "1px solid #ccc", paddingTop: 12 }}>
          <h3>
            Review: {selected.foodToReplace} <RequestStatusBadge status={selected.status} />
          </h3>
          <p>User: {selected.userName}</p>
          <p>Reason: {selected.reason}</p>
          {selected.suggestion && <p>Suggestion: {selected.suggestion}</p>}

          {selected.status === "pending" && (
            <SuggestionForm onSubmit={handleSuggest} disabled={busy} />
          )}

          {selected.status === "suggested" && (
            <div>
              <p>Waiting for the user. (Test buttons for the user's answer)</p>
              <button onClick={() => handleRespond(true)} disabled={busy}>Accept</button>{" "}
              <button onClick={() => handleRespond(false)} disabled={busy}>Reject</button>
            </div>
          )}

          {(selected.status === "accepted" || selected.status === "rejected") && (
            <p>This request is closed ({selected.status}).</p>
          )}
        </div>
      )}
    </div>
  );
}