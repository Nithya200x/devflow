import { useState, useEffect, useCallback } from 'react';
import { FiPlay, FiCheckCircle, FiXCircle, FiActivity, FiRotateCcw } from 'react-icons/fi';
import * as deploymentService from '../../services/deploymentService';
import { DataTable } from '../../components/Tables/DataTable';
import { LoadingSpinner } from '../../components/Common/LoadingSpinner';
import { NetworkError } from '../../components/Common/NetworkError';
import { EmptyState } from '../../components/Common/EmptyState';

export default function Deployments() {
  const [deployments, setDeployments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);

  const fetchDeployments = useCallback(async () => {
    try {
      const data = await deploymentService.getDeployments();
      setDeployments(data);
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDeployments();
  }, [fetchDeployments]);

  const triggerDeploy = async () => {
    setActionLoading(true);
    try {
      await deploymentService.createDeployment(1);
      await fetchDeployments();
    } catch (err) {
      setError(err);
    } finally {
      setActionLoading(false);
    }
  };

  const rollbackDeploy = async (deployId) => {
    setActionLoading(true);
    try {
      await deploymentService.rollbackDeployment(deployId);
      await fetchDeployments();
    } catch (err) {
      setError(err);
    } finally {
      setActionLoading(false);
    }
  };

  const columns = [
    { key: 'id', label: 'ID', style: { color: 'var(--text-secondary)' }, render: (row) => `#${row.id}` },
    { key: 'project_id', label: 'Project', render: (row) => <strong>Project {row.project_id}</strong> },
    { key: 'environment', label: 'Env', render: (row) => <span className="badge neutral">{row.environment}</span> },
    {
      key: 'status', label: 'Status',
      render: (row) => (
        <span className={`badge ${row.status}`}>
          {row.status === 'success' && <FiCheckCircle size={14} />}
          {row.status === 'failed' && <FiXCircle size={14} />}
          {row.status === 'running' && <FiActivity size={14} />}
          {row.status}
        </span>
      ),
    },
    { key: 'deployed_by', label: 'Deployed By', style: { color: 'var(--text-secondary)' } },
    {
      key: 'actions', label: 'Actions',
      render: (row) => (
        row.status === 'success' ? (
          <button className="btn btn-danger" style={{padding: '0.4rem 0.8rem', fontSize: '0.8rem'}} onClick={() => rollbackDeploy(row.id)} disabled={actionLoading}>
            <FiRotateCcw size={14} /> Rollback
          </button>
        ) : null
      ),
    },
  ];

  if (loading) return <LoadingSpinner />;
  if (error && !deployments.length) return <NetworkError error={error} onRetry={fetchDeployments} />;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Deployments</h1>
          <p className="page-subtitle">Track and orchestrate CI/CD pipelines.</p>
        </div>
        <button className="btn btn-primary" onClick={triggerDeploy} disabled={actionLoading}>
          <FiPlay size={18} /> Deploy Payment GW
        </button>
      </div>
      
      {error && <NetworkError error={error} onRetry={fetchDeployments} />}
      
      {!deployments.length && !error ? (
        <EmptyState message="No deployments found" />
      ) : (
        <DataTable columns={columns} data={deployments} />
      )}
    </div>
  );
}
