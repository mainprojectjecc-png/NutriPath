import RequestStatusBadge from "./RequestStatusBadge";

export default function RequestList({ requests, onSelect }) {
  return (
    <ul>
      {requests.map((r) => (
        <li key={r.id} onClick={() => onSelect(r)} style={{ cursor: "pointer", marginBottom: 8 }}>
          <strong>{r.userName}</strong>: {r.foodToReplace} <RequestStatusBadge status={r.status} />
        </li>
      ))}
    </ul>
  );
}