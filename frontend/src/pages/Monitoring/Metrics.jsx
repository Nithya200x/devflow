import { useState, useEffect, useCallback } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { FiArrowLeft, FiCpu, FiActivity, FiHardDrive, FiLayers, FiAlertTriangle, FiRefreshCw, FiBarChart2, FiServer } from 'react-icons/fi';
import { LoadingSpinner } from '../../components/Common/LoadingSpinner';
import { NetworkError } from '../../components/Common/NetworkError';
import { EmptyState } from '../../components/Common/EmptyState';
import * as prometheusService from '../../services/prometheusService';

const METRIC_TABS = [
  { key: 'cpu', label: 'CPU', icon: FiCpu },
  { key: 'memory', label: 'Memory', icon: FiActivity },
  { key: 'disk', label: 'Disk', icon: FiHardDrive },
  { key: 'network', label: 'Network', icon: FiLayers },
  { key: 'deployment', label: 'Deployments', icon: FiServer },
  { key: 'error', label: 'Error Rate', icon: FiAlertTriangle },
  { key: 'latency', label: 'Latency', icon: FiBarChart2 },
];

export default function PrometheusMetrics() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState(searchParams.get('type') || 'cpu');
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [namespace, setNamespace] = useState('');
  const [pod, setPod] = useState('');

  const fetchMetrics = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {};
      if (namespace) params.namespace = namespace;
      if (pod) params.pod = pod;

      let data;
      switch (activeTab) {
        case 'cpu':
          data = await prometheusService.getCPUMetrics(params);
          break;
        case 'memory':
          data = await prometheusService.getMemoryMetrics(params);
          break;
        case 'disk':
          data = await prometheusService.getDiskMetrics(params);
          break;
        case 'network':
          data = await prometheusService.getNetworkMetrics(params);
          break;
        case 'deployment':
          data = await prometheusService.getDeploymentMetrics(params);
          break;
        case 'error':
          data = await prometheusService.getErrorRate(params);
          break;
        case 'latency':
          data = await prometheusService.getLatency(params);
          break;
        default:
          data = await prometheusService.getCPUMetrics(params);
      }
      setMetrics(data);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, [activeTab, namespace, pod]);

  useEffect(() => { fetchMetrics(); }, [fetchMetrics]);

  return (
    <div>
      <div className="page-header">
        <div>
          <button className="btn" onClick={() => navigate('/monitoring')} style={{ marginBottom: '0.75rem' }}>
            <FiArrowLeft size={16} /> Back to Monitoring
          </button>
          <h1 className="page-title">Prometheus Metrics</h1>
          <p className="page-subtitle">Real-time infrastructure and application metrics.</p>
        </div>
        <button className="btn" onClick={fetchMetrics} disabled={loading}>
          <FiRefreshCw size={16} className={loading ? 'spin' : ''} /> Refresh
        </button>
      </div>

      <div className="tabs" style={{ marginBottom: '1.5rem' }}>
        {METRIC_TABS.map(tab => (
          <button key={tab.key}
            className={`tab ${activeTab === tab.key ? 'active' : ''}`}
            onClick={() => { setActiveTab(tab.key); setSearchParams({ type: tab.key }); }}>
            <tab.icon size={16} /> {tab.label}
          </button>
        ))}
      </div>

      <div className="glass-panel" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <div>
            <label className="deploy-info-label" style={{ display: 'block', marginBottom: '0.25rem' }}>Namespace</label>
            <input className="input" type="text" placeholder="default" value={namespace}
              onChange={e => setNamespace(e.target.value)} style={{ padding: '0.4rem 0.75rem', width: '200px' }} />
          </div>
          <div>
            <label className="deploy-info-label" style={{ display: 'block', marginBottom: '0.25rem' }}>Pod</label>
            <input className="input" type="text" placeholder="Optional" value={pod}
              onChange={e => setPod(e.target.value)} style={{ padding: '0.4rem 0.75rem', width: '200px' }} />
          </div>
          <button className="btn" onClick={fetchMetrics} style={{ marginTop: '1.2rem' }}>Filter</button>
        </div>
      </div>

      {loading ? <LoadingSpinner /> : error ? <NetworkError error={error} onRetry={fetchMetrics} /> : (
        <div className="glass-panel">
          <h3 style={{ marginBottom: '1rem', textTransform: 'capitalize' }}>{activeTab} Metrics</h3>
          {metrics && Object.keys(metrics).length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {Object.entries(metrics).map(([key, value]) => (
                <div key={key} style={{ padding: '0.75rem', background: 'rgba(255,255,255,0.03)', borderRadius: '4px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <code style={{ color: 'var(--accent-color)', fontSize: '0.85rem' }}>{key}</code>
                    <span className={`badge ${value?.status === 'success' ? 'success' : 'danger'}`}>{value?.status || 'unknown'}</span>
                  </div>
                  {value?.data?.result?.length > 0 ? (
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                      {value.data.result.map((r, i) => (
                        <div key={i} style={{ padding: '0.25rem 0', borderBottom: i < value.data.result.length - 1 ? '1px solid rgba(255,255,255,0.05)' : 'none' }}>
                          <span style={{ color: 'var(--text-primary)' }}>{r.value?.[1] || 'N/A'}</span>
                          {r.metric && Object.keys(r.metric).length > 0 && (
                            <span style={{ marginLeft: '0.5rem', opacity: 0.7 }}>
                              {Object.entries(r.metric).map(([k, v]) => `${k}="${v}"`).join(', ')}
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <EmptyState message={value?.error || 'No data returned'} />
                  )}
                </div>
              ))}
            </div>
          ) : (
            <EmptyState message="No metrics available. Is Prometheus connected?" />
          )}
        </div>
      )}
    </div>
  );
}
