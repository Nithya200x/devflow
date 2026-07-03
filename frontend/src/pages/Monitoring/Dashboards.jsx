import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiArrowLeft, FiPieChart, FiExternalLink, FiRefreshCw, FiGrid, FiList, FiSearch } from 'react-icons/fi';
import { LoadingSpinner } from '../../components/Common/LoadingSpinner';
import { NetworkError } from '../../components/Common/NetworkError';
import { EmptyState } from '../../components/Common/EmptyState';
import * as grafanaService from '../../services/grafanaService';

export default function GrafanaDashboards() {
  const navigate = useNavigate();
  const [dashboards, setDashboards] = useState([]);
  const [datasources, setDatasources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const [selectedDashboard, setSelectedDashboard] = useState(null);
  const [viewMode, setViewMode] = useState('grid');

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [dashData, dsData] = await Promise.all([
        grafanaService.listDashboards(),
        grafanaService.listDatasources(),
      ]);
      setDashboards(Array.isArray(dashData?.dashboards) ? dashData.dashboards : []);
      setDatasources(Array.isArray(dsData?.datasources) ? dsData.datasources : []);
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const filtered = dashboards.filter(d =>
    !search || d.title?.toLowerCase().includes(search.toLowerCase()) || d.tags?.some(t => t.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div>
      <div className="page-header">
        <div>
          <button className="btn" onClick={() => navigate('/monitoring')} style={{ marginBottom: '0.75rem' }}>
            <FiArrowLeft size={16} /> Back to Monitoring
          </button>
          <h1 className="page-title">Grafana Dashboards</h1>
          <p className="page-subtitle">Browse and link Grafana dashboards to incidents.</p>
        </div>
        <button className="btn" onClick={fetchData} disabled={loading}>
          <FiRefreshCw size={16} className={loading ? 'spin' : ''} /> Refresh
        </button>
      </div>

      <div className="glass-panel" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: '200px', position: 'relative' }}>
            <FiSearch size={14} style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)' }} />
            <input className="input" type="text" placeholder="Search dashboards..." value={search}
              onChange={e => setSearch(e.target.value)} style={{ padding: '0.5rem 0.75rem 0.5rem 2.25rem', width: '100%' }} />
          </div>
          <div style={{ display: 'flex', gap: '0.25rem', background: 'rgba(255,255,255,0.05)', borderRadius: '4px', padding: '0.2rem' }}>
            <button className={`btn btn-sm ${viewMode === 'grid' ? 'active' : ''}`} onClick={() => setViewMode('grid')}><FiGrid size={14} /></button>
            <button className={`btn btn-sm ${viewMode === 'list' ? 'active' : ''}`} onClick={() => setViewMode('list')}><FiList size={14} /></button>
          </div>
          <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>{filtered.length} dashboards</span>
        </div>
      </div>

      {loading ? <LoadingSpinner /> : error ? <NetworkError error={error} onRetry={fetchData} /> : (
        <>
          {datasources.length > 0 && (
            <div style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ marginBottom: '0.75rem', fontSize: '0.95rem' }}>Datasources</h3>
              <div className="grid-cards" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))' }}>
                {datasources.map(ds => (
                  <div key={ds.uid || ds.name} className="glass-panel" style={{ padding: '0.75rem' }}>
                    <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: '0.25rem' }}>{ds.name}</div>
                    <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>{ds.type} · {ds.url || ''}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {filtered.length > 0 ? (
            <div className={viewMode === 'grid' ? 'grid-cards' : ''} style={viewMode === 'list' ? { display: 'flex', flexDirection: 'column', gap: '0.5rem' } : {}}>
              {filtered.map(d => (
                <div key={d.uid} className={`glass-panel ${viewMode === 'list' ? '' : ''}`}
                  style={{ cursor: 'pointer', ...(viewMode === 'list' ? { padding: '0.75rem 1rem' } : {}) }}
                  onClick={() => setSelectedDashboard(selectedDashboard?.uid === d.uid ? null : d)}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <FiPieChart size={viewMode === 'grid' ? 20 : 16} style={{ color: 'var(--accent-color)' }} />
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{d.title}</div>
                      {d.tags?.length > 0 && (
                        <div style={{ display: 'flex', gap: '0.25rem', marginTop: '0.25rem', flexWrap: 'wrap' }}>
                          {d.tags.map(t => <span key={t} className="badge neutral" style={{ fontSize: '0.7rem' }}>{t}</span>)}
                        </div>
                      )}
                    </div>
                    {d.url && (
                      <a href={d.url} target="_blank" rel="noopener noreferrer" onClick={e => e.stopPropagation()}
                        style={{ color: 'var(--accent-color)' }}>
                        <FiExternalLink size={16} />
                      </a>
                    )}
                  </div>
                  {selectedDashboard?.uid === d.uid && (
                    <div style={{ marginTop: '1rem', padding: '0.75rem', background: 'rgba(255,255,255,0.03)', borderRadius: '4px', fontSize: '0.85rem' }}>
                      <div className="deploy-info-grid">
                        <div className="deploy-info-item">
                          <span className="deploy-info-label">UID</span>
                          <span className="deploy-info-value"><code>{d.uid}</code></span>
                        </div>
                        <div className="deploy-info-item">
                          <span className="deploy-info-label">Type</span>
                          <span className="deploy-info-value">{d.type || 'dash-db'}</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <EmptyState message={search ? 'No dashboards match your search' : 'No Grafana dashboards found. Is Grafana connected?'} />
          )}
        </>
      )}
    </div>
  );
}
