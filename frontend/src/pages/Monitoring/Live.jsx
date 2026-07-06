import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiArrowLeft, FiMonitor, FiExternalLink, FiRefreshCw } from 'react-icons/fi';
import { LoadingSpinner } from '../../components/Common/LoadingSpinner';
import config from '../../config/config';

export default function GrafanaLiveDashboard() {
  const navigate = useNavigate();
  const [iframeLoading, setIframeLoading] = useState(true);
  const [iframeError, setIframeError] = useState(false);

  const dashboardUrl = config.GRAFANA_DASHBOARD_URL;
  const embedUrl = dashboardUrl
    ? dashboardUrl.includes("?")
      ? `${dashboardUrl}&orgId=1&kiosk&theme=dark`
      : `${dashboardUrl}?orgId=1&kiosk&theme=dark`
    : "";

  const handleIframeLoad = () => {
    setIframeLoading(false);
    setIframeError(false);
  };

  const handleIframeError = () => {
    setIframeLoading(false);
    setIframeError(true);
  };

  const handleRetry = () => {
    setIframeError(false);
    setIframeLoading(true);
  };

  if (!dashboardUrl) {
    return (
      <div>
        <div className="page-header">
          <div>
            <button className="btn" onClick={() => navigate('/monitoring')} style={{ marginBottom: '0.75rem' }}>
              <FiArrowLeft size={16} /> Back to Monitoring
            </button>
            <h1 className="page-title">Live Dashboard</h1>
            <p className="page-subtitle">Embedded Grafana observability dashboard.</p>
          </div>
        </div>
        <div className="glass-panel" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
          <FiMonitor size={48} style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }} />
          <h3 style={{ marginBottom: '0.75rem' }}>Dashboard Not Configured</h3>
          <p style={{ color: 'var(--text-secondary)', maxWidth: '480px', margin: '0 auto' }}>
            Set the <code style={{ color: 'var(--accent-color)' }}>VITE_GRAFANA_DASHBOARD_URL</code> environment variable
            to embed a public Grafana dashboard. Use a{' '}
            <code style={{ color: 'var(--accent-color)' }}>/*?&kiosk=tv*/</code> URL for a full-screen kiosk view.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <button className="btn" onClick={() => navigate('/monitoring')} style={{ marginBottom: '0.75rem' }}>
            <FiArrowLeft size={16} /> Back to Monitoring
          </button>
          <h1 className="page-title">Live Dashboard</h1>
          <p className="page-subtitle">Real-time infrastructure observability powered by Grafana.</p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button className="btn" onClick={handleRetry} disabled={iframeLoading}>
            <FiRefreshCw size={16} className={iframeLoading ? 'spin' : ''} /> Reload
          </button>
          <a href={dashboardUrl} target="_blank" rel="noopener noreferrer" className="btn">
            <FiExternalLink size={16} /> Open in Grafana
          </a>
        </div>
      </div>

      <div className="glass-panel" style={{ padding: 0, overflow: 'hidden', position: 'relative', minHeight: '600px' }}>
        {iframeLoading && (
          <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-primary)', zIndex: 1 }}>
            <LoadingSpinner text="Loading dashboard..." />
          </div>
        )}

        {iframeError ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '4rem 2rem', height: '600px' }}>
            <FiMonitor size={48} style={{ color: 'var(--danger-color)', marginBottom: '1rem' }} />
            <h3 style={{ marginBottom: '0.75rem' }}>Dashboard Load Error</h3>
            <p style={{ color: 'var(--text-secondary)', maxWidth: '480px', textAlign: 'center', marginBottom: '1.5rem' }}>
              Unable to load the Grafana dashboard. Make sure the dashboard is published and accessible, or check the URL configuration.
            </p>
            <button className="btn btn-primary" onClick={handleRetry}>
              <FiRefreshCw size={16} /> Retry
            </button>
          </div>
        ) : (
          <iframe
            src={embedUrl}
            title="Grafana Live Dashboard"
            style={{
              width: '100%',
              height: 'calc(100vh - 280px)',
              minHeight: '600px',
              border: 'none',
              display: 'block',
            }}
            onLoad={handleIframeLoad}
            onError={handleIframeError}
            allow="fullscreen"
          />
        )}
      </div>
    </div>
  );
}
