
export default function StatCard({
  title,
  value,
  unit,
  note,
  icon: Icon,
  color,
  progress
}) {
  return (
    <div className="stat-card">
      <div className="stat-top">
        <div>
          <p className="muted">{title}</p>
          <h2>{value}<small> {unit}</small></h2>
        </div>

        <div className={`stat-icon ${color}`}>
          <Icon size={22} />
        </div>
      </div>

      {progress !== undefined && (
        <div className="progress-track">
          <div
            className={`progress-fill ${color}`}
            style={{ width: `${progress}%` }}
          />
        </div>
      )}

      <span className="stat-note">{note}</span>
    </div>
  );
}
