export const STATUS_LABELS = {
  healthy: 'Healthy',
  available_locally: 'Available Locally',
  connected: 'Connected',
  configured: 'Configured',
  not_configured: 'Not Configured',
  remote_unavailable: 'Remote Unavailable',
  authentication_failed: 'Auth Failed',
  connection_failed: 'Connection Failed',
  unreachable: 'Unreachable',
  remote_environment: 'Remote',
  disabled: 'Disabled',
  degraded: 'Degraded',
  service_unavailable: 'Service Unavailable',
  unknown: 'Unknown',
  offline: 'Offline',
};

const HEALTHY_STATUSES = ['healthy', 'connected', 'configured'];
const WARNING_STATUSES = ['available_locally', 'remote_environment', 'remote_unavailable', 'degraded', 'warning', 'service_unavailable'];
const ERROR_STATUSES = ['authentication_failed', 'connection_failed', 'unreachable'];

export function getStatusClass(status) {
  if (!status) return 'offline';
  if (HEALTHY_STATUSES.includes(status)) return 'online';
  if (WARNING_STATUSES.includes(status)) return 'warning';
  return 'offline';
}

export function getStatusColor(status) {
  const colors = {
    healthy: '#10b981', connected: '#10b981', configured: '#10b981',
    available_locally: '#0ea5e9', remote_environment: '#0ea5e9', degraded: '#f59e0b', service_unavailable: '#f59e0b',
    remote_unavailable: '#f59e0b',
    not_configured: '#6b7280', disabled: '#6b7280',
    authentication_failed: '#ef4444', connection_failed: '#ef4444', unreachable: '#ef4444',
    unknown: '#9ca3af', offline: '#9ca3af',
  };
  return colors[status] || '#9ca3af';
}

export function getStatusLabel(status) {
  return STATUS_LABELS[status] || (typeof status === 'string' ? status.charAt(0).toUpperCase() + status.slice(1) : 'Unknown');
}

export function StatusBadge({ status, className = '', style = {} }) {
  const cls = getStatusClass(status);
  const label = getStatusLabel(status);
  const color = getStatusColor(status);
  return (
    <span className={`badge ${cls} ${className}`} style={{ ...style, color, borderColor: color }}>
      {label}
    </span>
  );
}

export function HealthStatus({ name, icon: Icon, status, detail }) {
  const dotClass = getStatusClass(status);
  const label = getStatusLabel(status);
  return (
    <div className="health-item" title={detail || label}>
      <div className={`health-dot ${dotClass}`} />
      {Icon && <Icon size={14} style={{ color: 'var(--text-secondary)', flexShrink: 0 }} />}
      <span className="health-label">{name}</span>
      <span className={`health-status ${dotClass}`}>{label}</span>
    </div>
  );
}
