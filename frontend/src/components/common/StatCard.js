/**
 * components/common/StatCard.js
 * Dashboard KPI card with icon, value, and label.
 */
export default function StatCard({ icon, value, label, color = 'var(--accent)', bg }) {
  const bgColor = bg || `${color}22`;
  return (
    <div className="stat-card">
      <div className="stat-icon" style={{ background: bgColor, color }}>
        {icon}
      </div>
      <div className="stat-info">
        <div className="stat-value">{value ?? '—'}</div>
        <div className="stat-label">{label}</div>
      </div>
    </div>
  );
}
