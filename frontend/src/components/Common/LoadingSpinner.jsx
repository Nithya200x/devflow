import { FiLoader } from 'react-icons/fi';

export function LoadingSpinner({ message = 'Loading...' }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '3rem', gap: '1rem' }}>
      <FiLoader size={32} className="spin" />
      <p style={{ color: 'var(--text-secondary)' }}>{message}</p>
    </div>
  );
}
