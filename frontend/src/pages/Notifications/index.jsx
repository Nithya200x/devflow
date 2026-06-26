import { FiMail, FiSlack, FiMessageSquare, FiGlobe, FiBell, FiSettings } from 'react-icons/fi';
import { EmptyState } from '../../components/Common/EmptyState';

const PROVIDERS = [
  { name: 'Email', icon: FiMail, description: 'SMTP-based email notifications for incident alerts.' },
  { name: 'Slack', icon: FiMessageSquare, description: 'Real-time Slack channel notifications.' },
  { name: 'Microsoft Teams', icon: FiBell, description: 'Teams webhook integration for incident updates.' },
  { name: 'Discord', icon: FiGlobe, description: 'Discord webhook notifications.' },
  { name: 'Webhooks', icon: FiSettings, description: 'Custom HTTP webhook endpoints.' },
];

export default function Notifications() {
  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Notifications</h1>
          <p className="page-subtitle">Configure notification providers for incident alerts.</p>
        </div>
      </div>

      <div className="grid-cards" style={{ marginBottom: '2.5rem' }}>
        {PROVIDERS.map(provider => (
          <div key={provider.name} className="glass-panel" style={{ opacity: 0.6 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
              <div className="stat-icon blue">
                <provider.icon size={24} />
              </div>
              <div>
                <h3 style={{ margin: 0 }}>{provider.name}</h3>
              </div>
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '1rem' }}>
              {provider.description}
            </p>
            <EmptyState message="Coming in next phase" />
          </div>
        ))}
      </div>

      <div className="glass-panel">
        <h3>Notification Interface</h3>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
          The notification system is designed around a provider-agnostic interface.
        </p>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', fontFamily: 'var(--mono-font)' }}>
          NotificationService.register(emailProvider)
        </p>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', fontFamily: 'var(--mono-font)', marginTop: '0.25rem' }}>
          NotificationService.register(slackProvider)
        </p>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '1rem' }}>
          Providers will be pluggable via the NotificationProvider interface. No provider implementations are included yet.
        </p>
      </div>
    </div>
  );
}
