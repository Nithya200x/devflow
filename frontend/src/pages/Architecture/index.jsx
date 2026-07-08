import { FiMonitor, FiServer, FiDatabase, FiGitBranch, FiBox, FiLayers, FiBarChart2, FiAlertTriangle, FiPieChart, FiActivity, FiCpu } from 'react-icons/fi';

const layers = [
  {
    title: 'Frontend',
    icon: FiMonitor,
    description: 'React SPA with Recharts, lucide-react icons, and custom glassmorphism design. Communicates with the backend via REST API.',
    color: '#3b82f6',
    arrow: '↓',
  },
  {
    title: 'Backend API',
    icon: FiServer,
    description: 'Flask REST API serving the frontend. JWT authentication, Prometheus metrics, gunicorn WSGI.',
    color: '#8b5cf6',
    arrow: '↓',
  },
  {
    title: 'Orchestration Engine',
    icon: FiActivity,
    description: 'Event-driven incident detection and correlation engine. Collectors for GitHub, Docker, K8s, Prometheus, and Grafana.',
    color: '#f59e0b',
    arrow: '↓ →',
  },
  {
    title: 'GitHub',
    icon: FiGitBranch,
    description: 'GitHub API integration for repositories, pull requests, commits, branches, and workflow dispatch.',
    color: '#22c55e',
    arrow: '',
  },
  {
    title: 'Docker',
    icon: FiBox,
    description: 'Docker Engine API for container management, image operations, and real-time stats.',
    color: '#0ea5e9',
    arrow: '',
  },
  {
    title: 'Kubernetes',
    icon: FiLayers,
    description: 'Kubernetes API for pod, deployment, service, ingress, and rollout management via kubeconfig.',
    color: '#3b82f6',
    arrow: '',
  },
  {
    title: 'Prometheus',
    icon: FiBarChart2,
    description: 'Prometheus HTTP API for metric queries, alert rules, and real-time monitoring data.',
    color: '#ef4444',
    arrow: '',
  },
  {
    title: 'Alertmanager',
    icon: FiAlertTriangle,
    description: 'Alertmanager API for alert routing, silencing, and webhook forwarding to the orchestration engine.',
    color: '#f97316',
    arrow: '',
  },
  {
    title: 'Grafana',
    icon: FiPieChart,
    description: 'Grafana API for dashboard management, datasource provisioning, and visualization.',
    color: '#f59e0b',
    arrow: '',
  },
  {
    title: 'Incident Engine',
    icon: FiAlertTriangle,
    description: 'Incident lifecycle management: creation, correlation, timeline tracking, resolution, and AI analysis.',
    color: '#ec4899',
    arrow: '↓',
  },
  {
    title: 'AI Root Cause Analysis',
    icon: FiCpu,
    description: 'Groq-powered AI analysis for root cause identification, fix suggestions, and risk assessment.',
    color: '#a855f7',
    arrow: '',
  },
  {
    title: 'PostgreSQL',
    icon: FiDatabase,
    description: 'Primary database for users, projects, deployments, incidents, events, AI analyses, and configurations.',
    color: '#06b6d4',
    arrow: '',
  },
];

function LayerCard({ layer, index }) {
  return (
    <div className="glass-panel" style={{ borderLeft: `3px solid ${layer.color}`, marginBottom: '0.75rem' }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '1rem' }}>
        <div style={{
          width: 40, height: 40, borderRadius: 10, background: `${layer.color}20`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          flexShrink: 0, color: layer.color,
        }}>
          <layer.icon size={20} />
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 600, fontSize: '0.95rem', marginBottom: '0.25rem' }}>{layer.title}</div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.82rem', margin: 0 }}>{layer.description}</p>
        </div>
      </div>
    </div>
  );
}

export default function Architecture() {
  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">System Architecture</h1>
          <p className="page-subtitle">End-to-end architecture of the DevFlow platform.</p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
        <div>
          {layers.map((layer, i) => (
            <div key={i}>
              <LayerCard layer={layer} index={i} />
              {layer.arrow && (
                <div style={{ textAlign: 'center', padding: '0.25rem 0', color: 'var(--text-secondary)', fontSize: '1.2rem' }}>
                  {layer.arrow}
                </div>
              )}
            </div>
          ))}
        </div>

        <div>
          <div className="glass-panel" style={{ marginBottom: '1rem' }}>
            <h3 style={{ marginBottom: '0.75rem', fontSize: '0.95rem' }}>Data Flow</h3>
            <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: '1.7' }}>
              <p>1. User interacts with the <strong>Frontend</strong> React SPA.</p>
              <p>2. Frontend calls the <strong>Backend API</strong> via REST endpoints.</p>
              <p>3. Backend queries <strong>PostgreSQL</strong> for persistent data.</p>
              <p>4. <strong>Orchestration Engine</strong> polls 6 collectors for evidence.</p>
              <p>5. <strong>Prometheus detector</strong> checks alert rules every 30s.</p>
              <p>6. Alerts fire to <strong>Alertmanager</strong>, which webhooks the backend.</p>
              <p>7. Backend creates incidents and triggers <strong>AI Root Cause Analysis</strong> via Groq.</p>
              <p>8. <strong>Grafana</strong> provides dashboards from Prometheus data.</p>
              <p>9. <strong>GitHub Actions</strong> handles CI/CD workflow dispatch.</p>
              <p>10. <strong>Docker</strong> and <strong>Kubernetes</strong> provide container orchestration.</p>
            </div>
          </div>

          <div className="glass-panel">
            <h3 style={{ marginBottom: '0.75rem', fontSize: '0.95rem' }}>Technology Stack</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', fontSize: '0.82rem' }}>
              {[
                ['Frontend', 'React 19, Vite 8, Recharts'],
                ['Backend', 'Flask, gunicorn, SQLAlchemy'],
                ['Database', 'PostgreSQL 15'],
                ['Container', 'Docker, Docker Compose'],
                ['Orchestration', 'Kubernetes (minikube)'],
                ['Monitoring', 'Prometheus, Grafana'],
                ['Alerting', 'Alertmanager'],
                ['AI', 'Groq (Llama 3.3 70B)'],
                ['CI/CD', 'GitHub Actions'],
                ['Auth', 'JWT, bcrypt'],
              ].map(([label, value]) => (
                <div key={label}>
                  <div style={{ color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>{label}</div>
                  <div style={{ fontWeight: 600 }}>{value}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
