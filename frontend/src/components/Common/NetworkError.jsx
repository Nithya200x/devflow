import { FiAlertCircle, FiXCircle } from 'react-icons/fi';
import config from '../../config/config';

export function NetworkError({ error, onRetry }) {
  const isUnauthorized = error?.response?.status === 401;
  const isNetwork = !error?.response;

  if (isUnauthorized) return null;

  return (
    <div className="glass-panel" style={{ textAlign: 'center', padding: '2rem', marginBottom: '1.5rem' }}>
      {isNetwork ? <FiXCircle size={36} style={{ color: 'var(--danger-color)', marginBottom: '0.75rem' }} /> : <FiAlertCircle size={36} style={{ color: 'var(--warning-color)', marginBottom: '0.75rem' }} />}
      <h3 style={{ color: isNetwork ? 'var(--danger-color)' : 'var(--warning-color)', marginBottom: '0.5rem' }}>
        {isNetwork ? 'Network Error' : 'Request Failed'}
      </h3>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '0.5rem', fontSize: '0.9rem' }}>
        {isNetwork
          ? `Unable to reach the server at ${config.API_URL}. Please check that the backend is running.`
          : error?.response?.data?.msg || error?.message || 'An unexpected error occurred.'}
      </p>
      {onRetry && (
        <button className="btn btn-primary" onClick={onRetry} style={{ marginTop: '0.75rem' }}>
          Retry
        </button>
      )}
    </div>
  );
}
