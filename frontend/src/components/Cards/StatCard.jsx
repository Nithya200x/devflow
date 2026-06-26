export function StatCard({ icon: Icon, label, value, color = 'blue' }) {
  return (
    <div className="glass-panel stat-card">
      <div className={`stat-icon ${color}`}><Icon /></div>
      <div className="stat-content">
        <h3>{label}</h3>
        <p>{value}</p>
      </div>
    </div>
  );
}
