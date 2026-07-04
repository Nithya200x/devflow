import { useState, useEffect, useCallback } from 'react';
import { FiCheckCircle } from 'react-icons/fi';
import * as incidentService from '../../services/incidentService';
import { DataTable } from '../../components/Tables/DataTable';
import { LoadingSpinner } from '../../components/Common/LoadingSpinner';
import { NetworkError } from '../../components/Common/NetworkError';
import { EmptyState } from '../../components/Common/EmptyState';

export default function Incidents() {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchIncidents = useCallback(async () => {
    try {
      const data = await incidentService.getIncidents();
      setIncidents(data);
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchIncidents();
  }, [fetchIncidents]);

  const resolveIncident = async (id) => {
    try {
      await incidentService.resolveIncident(id);
      await fetchIncidents();
    } catch (err) {
      setError(err);
    }
  };

  const columns = [
    { key: 'id', label: 'ID', style: { color: 'var(--text-secondary)' }, render: (row) => `#${row.id}` },
    { key: 'title', label: 'Title', render: (row) => <strong>{row.title}</strong> },
    { key: 'severity', label: 'Severity', render: (row) => <span className={`badge ${row.severity}`}>{row.severity}</span> },
    { key: 'status', label: 'Status', render: (row) => <span className={`badge ${row.status}`}>{row.status}</span> },
    { key: 'created_at', label: 'Created', style: { color: 'var(--text-secondary)' }, render: (row) => new Date(row.created_at).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' }) },
    {
      key: 'actions', label: 'Actions',
      render: (row) => (
        row.status !== 'resolved' ? (
          <button className="btn btn-success" style={{padding: '0.4rem 0.8rem', fontSize: '0.8rem'}} onClick={() => resolveIncident(row.id)}>
            <FiCheckCircle size={14} /> Resolve
          </button>
        ) : null
      ),
    },
  ];

  if (loading) return <LoadingSpinner />;
  if (error) return <NetworkError error={error} onRetry={fetchIncidents} />;
  if (!incidents.length) return <EmptyState message="No incidents found" />;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Incidents</h1>
          <p className="page-subtitle">Track and resolve platform alerts.</p>
        </div>
      </div>
      <DataTable columns={columns} data={incidents} />
    </div>
  );
}
