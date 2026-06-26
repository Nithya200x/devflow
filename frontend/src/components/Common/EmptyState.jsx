import { FiInbox } from 'react-icons/fi';

export function EmptyState({ message = 'No data available', icon: Icon = FiInbox }) {
  return (
    <div style={{ textAlign: 'center', padding: '3rem' }}>
      <Icon size={40} style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }} />
      <p style={{ color: 'var(--text-secondary)' }}>{message}</p>
    </div>
  );
}
