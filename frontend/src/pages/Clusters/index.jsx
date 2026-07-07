import { useState, useEffect, useCallback } from 'react';
import { FiServer, FiBox, FiActivity, FiList } from 'react-icons/fi';
import * as k8sService from '../../services/kubernetesService';
import { LoadingSpinner } from '../../components/Common/LoadingSpinner';
import { NetworkError } from '../../components/Common/NetworkError';
import { EmptyState } from '../../components/Common/EmptyState';
import { usePolling } from '../../hooks/usePolling';

function HealthCard({ health }) {
  if (!health || !health.connected) {
    return (
      <div className="glass-panel" style={{ gridColumn: '1 / -1' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
          <FiServer size={18} />
          <h3 style={{ margin: 0, fontSize: '0.95rem' }}>Cluster Health</h3>
          <span className="badge danger">Disconnected</span>
        </div>
        <p style={{ color: 'var(--text-secondary)', margin: 0 }}>
          {health?.reason || 'Kubernetes cluster is not reachable'}
        </p>
      </div>
    );
  }

  return (
    <div className="glass-panel" style={{ gridColumn: '1 / -1' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
        <FiServer size={18} />
        <h3 style={{ margin: 0, fontSize: '0.95rem' }}>Cluster Health</h3>
        <span className="badge success">Connected</span>
      </div>
      <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
        <div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Nodes</div>
          <div style={{ fontSize: '1.5rem', fontWeight: '700', color: '#fff' }}>
            {health.nodes_ready}<span style={{ color: 'var(--text-secondary)', fontSize: '1rem' }}> / {health.nodes_total}</span>
          </div>
        </div>
        <div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Pods Running</div>
          <div style={{ fontSize: '1.5rem', fontWeight: '700', color: '#22c55e' }}>{health.pods_running}</div>
        </div>
        <div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Pods Failed</div>
          <div style={{ fontSize: '1.5rem', fontWeight: '700', color: health.pods_failed > 0 ? '#ef4444' : 'var(--text-secondary)' }}>{health.pods_failed}</div>
        </div>
      </div>
    </div>
  );
}

function NotConfiguredSection({ icon: Icon, title, reason }) {
  return (
    <div className="glass-panel" style={{ gridColumn: '1 / -1' }}>
      <h3 style={{ fontSize: '0.95rem', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <Icon /> {title}
      </h3>
      <EmptyState
        icon={FiServer}
        message="Connect Cluster"
        description={reason || 'Configure kubeconfig to connect to a Kubernetes cluster'}
        action={{ label: 'Configure Kubernetes', onClick: () => {} }}
      />
    </div>
  );
}

function PodsTable({ pods }) {
  if (!pods || pods.length === 0) {
    return (
      <div className="glass-panel" style={{ gridColumn: '1 / -1' }}>
        <h3 style={{ fontSize: '0.95rem', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <FiBox /> Pods
        </h3>
        <EmptyState icon={FiBox} message="No pods found" description="No pods are running in this cluster" />
      </div>
    );
  }

  return (
    <div className="glass-panel" style={{ gridColumn: '1 / -1' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
        <FiBox size={18} />
        <h3 style={{ margin: 0, fontSize: '0.95rem' }}>Pods</h3>
        <span className="badge info">{pods.length} total</span>
      </div>
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Namespace</th>
              <th>Status</th>
              <th>Restarts</th>
              <th>Age</th>
            </tr>
          </thead>
          <tbody>
            {pods.slice(0, 50).map((pod, i) => (
              <tr key={pod.name || i}>
                <td style={{ fontWeight: 600, fontFamily: 'var(--mono-font)', fontSize: '0.8rem' }}>{pod.name}</td>
                <td style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>{pod.namespace}</td>
                <td>
                  <span className={`badge ${pod.status === 'Running' ? 'success' : pod.status === 'Pending' ? 'pending' : 'danger'}`}>
                    {pod.status}
                  </span>
                </td>
                <td style={{ fontFamily: 'var(--mono-font)', fontSize: '0.8rem' }}>{pod.restart_count}</td>
                <td style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>{pod.start_time ? new Date(pod.start_time).toLocaleString() : '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function DeploymentsTable({ deployments }) {
  if (!deployments || deployments.length === 0) {
    return (
      <div className="glass-panel" style={{ gridColumn: '1 / -1' }}>
        <h3 style={{ fontSize: '0.95rem', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <FiActivity /> Deployments
        </h3>
        <p style={{ color: 'var(--text-secondary)', margin: 0 }}>No deployments found</p>
      </div>
    );
  }

  return (
    <div className="glass-panel" style={{ gridColumn: '1 / -1' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
        <FiActivity size={18} />
        <h3 style={{ margin: 0, fontSize: '0.95rem' }}>Deployments</h3>
        <span className="badge info">{deployments.length} total</span>
      </div>
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Namespace</th>
              <th>Ready</th>
              <th>Desired</th>
              <th>Available</th>
            </tr>
          </thead>
          <tbody>
            {deployments.map((dep, i) => (
              <tr key={dep.name || i}>
                <td style={{ fontWeight: 600, fontFamily: 'var(--mono-font)', fontSize: '0.8rem' }}>{dep.name}</td>
                <td style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>{dep.namespace}</td>
                <td>
                  <span className={`badge ${dep.ready_replicas > 0 ? 'success' : 'danger'}`}>
                    {dep.ready_replicas}
                  </span>
                </td>
                <td style={{ fontFamily: 'var(--mono-font)', fontSize: '0.8rem' }}>{dep.replicas}</td>
                <td style={{ fontFamily: 'var(--mono-font)', fontSize: '0.8rem' }}>{dep.available_replicas}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ServicesTable({ services }) {
  if (!services || services.length === 0) {
    return (
      <div className="glass-panel" style={{ gridColumn: '1 / -1' }}>
        <h3 style={{ fontSize: '0.95rem', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <FiList /> Services
        </h3>
        <p style={{ color: 'var(--text-secondary)', margin: 0 }}>No services found</p>
      </div>
    );
  }

  return (
    <div className="glass-panel" style={{ gridColumn: '1 / -1' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
        <FiList size={18} />
        <h3 style={{ margin: 0, fontSize: '0.95rem' }}>Services</h3>
        <span className="badge info">{services.length} total</span>
      </div>
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Namespace</th>
              <th>Type</th>
              <th>Cluster IP</th>
              <th>Ports</th>
            </tr>
          </thead>
          <tbody>
            {services.map((svc, i) => (
              <tr key={svc.name || i}>
                <td style={{ fontWeight: 600, fontFamily: 'var(--mono-font)', fontSize: '0.8rem' }}>{svc.name}</td>
                <td style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>{svc.namespace}</td>
                <td><span className="badge neutral">{svc.type}</span></td>
                <td style={{ fontFamily: 'var(--mono-font)', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{svc.cluster_ip}</td>
                <td style={{ fontFamily: 'var(--mono-font)', fontSize: '0.8rem' }}>
                  {svc.ports && svc.ports.map(p => `${p.port}${p.protocol ? '/' + p.protocol : ''}`).join(', ')}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function isNotConfigured(response) {
  return response && response.configured === false;
}

export default function Clusters() {
  const [health, setHealth] = useState(null);
  const [pods, setPods] = useState([]);
  const [podsNotConfigured, setPodsNotConfigured] = useState(false);
  const [deployments, setDeployments] = useState([]);
  const [depNotConfigured, setDepNotConfigured] = useState(false);
  const [services, setServices] = useState([]);
  const [svcNotConfigured, setSvcNotConfigured] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchAll = useCallback(async () => {
    try {
      const [healthData, podsData, depData, svcData] = await Promise.all([
        k8sService.getKubernetesHealth().catch(() => ({ connected: false })),
        k8sService.listPods().catch(() => ({ pods: [], count: 0, configured: false, reason: 'Kubernetes not connected' })),
        k8sService.listDeployments().catch(() => ({ deployments: [], count: 0, configured: false, reason: 'Kubernetes not connected' })),
        k8sService.listServices().catch(() => ({ services: [], count: 0, configured: false, reason: 'Kubernetes not connected' })),
      ]);
      setHealth(healthData);
      setPodsNotConfigured(isNotConfigured(podsData));
      setPods(podsData.pods || []);
      setDepNotConfigured(isNotConfigured(depData));
      setDeployments(depData.deployments || []);
      setSvcNotConfigured(isNotConfigured(svcData));
      setServices(svcData.services || []);
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  usePolling(fetchAll, 10000);

  if (loading) return <LoadingSpinner />;
  if (error) return <NetworkError error={error} onRetry={fetchAll} />;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Kubernetes</h1>
          <p className="page-subtitle">Real-time cluster monitoring from the Kubernetes API.</p>
        </div>
      </div>

      <div className="grid-cards stagger-children">
        <HealthCard health={health} />
        {podsNotConfigured ? (
          <NotConfiguredSection icon={FiBox} title="Pods" reason={health?.reason || 'Kubernetes cluster not connected'} />
        ) : (
          <PodsTable pods={pods} />
        )}
        {depNotConfigured ? (
          <NotConfiguredSection icon={FiActivity} title="Deployments" reason={health?.reason || 'Kubernetes cluster not connected'} />
        ) : (
          <DeploymentsTable deployments={deployments} />
        )}
        {svcNotConfigured ? (
          <NotConfiguredSection icon={FiList} title="Services" reason={health?.reason || 'Kubernetes cluster not connected'} />
        ) : (
          <ServicesTable services={services} />
        )}
      </div>
    </div>
  );
}
