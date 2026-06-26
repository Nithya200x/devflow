import { FiAlertCircle } from 'react-icons/fi';

export function ErrorMessage({ message = 'Something went wrong', onRetry }) {
  return (
    <div className="glass-panel" style={{ textAlign: 'center', padding: '3rem' }}>
      <FiAlertCircle size={40} style={{ color: 'var(--danger-color)', marginBottom: '1rem' }} />
      <h3 style={{ color: 'var(--danger-color)' }}>Error</h3>
      <p style={{ color: 'var(--text-secondary)', margin: '0.5rem 0 1.5rem' }}>{message}</p>
      {onRetry && (
        <button className="btn btn-primary" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
}
