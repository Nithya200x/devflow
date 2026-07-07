import { FiBell } from 'react-icons/fi';

export default function Notifications() {
  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Notifications</h1>
          <p className="page-subtitle">Configure notification providers for incident alerts.</p>
        </div>
      </div>
      <div className="glass-panel" style={{ textAlign: 'center', padding: '3rem' }}>
        <FiBell size={40} style={{ color: 'var(--text-muted)', marginBottom: '1rem' }} />
        <h3 style={{ marginBottom: '0.5rem' }}>Notification Providers Not Installed</h3>
        <p style={{ color: 'var(--text-secondary)', maxWidth: '480px', margin: '0 auto', fontSize: '0.85rem' }}>
          No notification provider implementations are configured. The orchestration engine supports
          Email, Slack, Microsoft Teams, Discord, and custom Webhook providers via a pluggable
          NotificationProvider interface. Configure providers via environment variables or
          the notification API to receive alerts for incidents, deployment failures, and system events.
        </p>
      </div>
    </div>
  );
}
