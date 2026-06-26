import { useState, useEffect, useCallback, useRef } from 'react';
import { FiCpu, FiHardDrive } from 'react-icons/fi';
import * as clusterService from '../../services/clusterService';
import { LogViewer } from '../../components/Terminal/LogViewer';
import { LoadingSpinner } from '../../components/Common/LoadingSpinner';
import { NetworkError } from '../../components/Common/NetworkError';
import { usePolling } from '../../hooks/usePolling';

export default function Clusters() {
  const [clusters, setClusters] = useState([]);
  const [logs, setLogs] = useState([]);
  const [selectedCluster, setSelectedCluster] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchClusters = useCallback(async () => {
    try {
      const data = await clusterService.getClusters();
      setClusters(data);
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchClusters();
  }, [fetchClusters]);

  usePolling(fetchClusters, 5000, !error);

  useEffect(() => {
    if (!selectedCluster) return;
    const interval = setInterval(async () => {
      try {
        const data = await clusterService.getClusterLogs(selectedCluster);
        setLogs(prev => [...prev, ...data.logs].slice(-30));
      } catch {
      }
    }, 3000);
    return () => clearInterval(interval);
  }, [selectedCluster]);

  const handleClusterSelect = (id) => {
    setSelectedCluster(id);
    setLogs([]);
  };

  if (loading) return <LoadingSpinner />;
  if (error) return <NetworkError error={error} onRetry={fetchClusters} />;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Clusters</h1>
          <p className="page-subtitle">Real-time node status and telemetry.</p>
        </div>
      </div>

      <div className="grid-cards" style={{ marginBottom: '2.5rem' }}>
        {clusters.map(c => (
          <div 
            key={c.id} 
            className="glass-panel" 
            style={{ 
              cursor: 'pointer', 
              borderColor: selectedCluster === c.id ? 'rgba(59, 130, 246, 0.5)' : '',
              boxShadow: selectedCluster === c.id ? '0 0 0 2px rgba(59, 130, 246, 0.3)' : ''
            }} 
            onClick={() => handleClusterSelect(c.id)}
          >
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem'}}>
              <div>
                <h3 style={{ margin: 0, color: '#fff' }}>{c.name}</h3>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>ID: #{c.id}</span>
              </div>
              <span className={`badge ${c.status}`}>{c.status}</span>
            </div>
            
            <div style={{ display: 'flex', gap: '1.5rem', marginBottom: '1.5rem' }}>
              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Nodes</div>
                <div style={{ fontSize: '1.25rem', fontWeight: '700', color: '#fff' }}>{c.node_count}</div>
              </div>
              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Pods</div>
                <div style={{ fontSize: '1.25rem', fontWeight: '700', color: '#fff' }}>{c.pod_count}</div>
              </div>
            </div>

            <div className="progress-container">
              <div className="progress-header">
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><FiCpu /> CPU Usage</span>
                <span style={{ color: c.cpu_percent > 80 ? 'var(--danger-color)' : '#fff' }}>{c.cpu_percent}%</span>
              </div>
              <div className="progress-track">
                <div className="progress-fill" style={{ 
                  width: `${c.cpu_percent}%`, 
                  background: c.cpu_percent > 80 ? 'var(--danger-color)' : 'var(--accent-color)'
                }}></div>
              </div>
            </div>

            <div className="progress-container">
              <div className="progress-header">
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><FiHardDrive /> Memory</span>
                <span style={{ color: c.mem_percent > 80 ? 'var(--warning-color)' : '#fff' }}>{c.mem_percent}%</span>
              </div>
              <div className="progress-track">
                <div className="progress-fill" style={{ 
                  width: `${c.mem_percent}%`, 
                  background: c.mem_percent > 80 ? 'var(--warning-color)' : 'var(--success-color)' 
                }}></div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {selectedCluster && (
        <LogViewer 
          logs={logs} 
          title={`Live Logs: ${clusters.find(c => c.id === selectedCluster)?.name}`}
        />
      )}
    </div>
  );
}
