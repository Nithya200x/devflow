import { FiInbox } from 'react-icons/fi';

export function EmptyState({ message = 'No data available', description, icon: Icon = FiInbox, action }) {
  return (
    <div className="empty-state">
      <Icon size={36} />
      <h3>{message}</h3>
      {description && <p>{description}</p>}
      {action && (
        <button className="btn btn-primary" style={{ marginTop: '1rem' }} onClick={action.onClick}>
          {action.label}
        </button>
      )}
    </div>
  );
}
