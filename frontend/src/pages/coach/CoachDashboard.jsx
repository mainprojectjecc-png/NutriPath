import { useState } from "react";
import { mockRequests } from "../../mock/coachMockData";
import RequestList from "../../components/coach/RequestList";
import SuggestionForm from "../../components/coach/SuggestionForm";

export default function CoachDashboard() {
  const [requests, setRequests] = useState(mockRequests);
  const [selected, setSelected] = useState(null);

  const sendSuggestion = (text) => {
    setRequests((prev) => prev.map((r) => (r.id === selected.id ? { ...r, suggestion: text, status: "suggested" } : r)));
    setSelected(null);
  };

  return (
    <div>
      <h2>Coach Dashboard</h2>
      <RequestList requests={requests} onSelect={setSelected} />
      {selected && (
        <div>
          <h3>Review: {selected.foodToReplace}</h3>
          <p>Reason: {selected.reason}</p>
          <SuggestionForm onSubmit={sendSuggestion} />
        </div>
      )}
    </div>
  );
}