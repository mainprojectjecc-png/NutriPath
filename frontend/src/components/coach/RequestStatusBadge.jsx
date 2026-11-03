const colors = { pending: "#f59e0b", suggested: "#3b82f6", accepted: "#16a34a", rejected: "#dc2626" };

export default function RequestStatusBadge({ status }) {
  return <span style={{ background: colors[status], color: "#fff", padding: "2px 10px", borderRadius: 12 }}>{status}</span>;
}