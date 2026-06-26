import React, { useState, useEffect } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import axios from 'axios';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer } from 'recharts';
import { 
  FiLayout, FiBox, FiServer, FiAlertTriangle, FiLogOut, 
  FiPlay, FiRotateCcw, FiCheckCircle, FiXCircle, FiActivity,
  FiTerminal, FiCpu, FiHardDrive, FiLayers, FiShield
} from 'react-icons/fi';

const API_URL = 'http://localhost:5000/api/v1';

// Setup Axios Interceptor for Auth
axios.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const Login = () => {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('admin123');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const res = await axios.post(`${API_URL}/auth/login`, { username, password });
      localStorage.setItem('token', res.data.access_token);
      localStorage.setItem('user', JSON.stringify(res.data.user));
      navigate('/');
    } catch (err) {
      setError('Invalid credentials');
    }
  };

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', width: '100vw' }}>
      <div className="glass-panel" style={{ width: '100%', maxWidth: '420px', padding: '2.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1.5rem' }}>
          <div className="sidebar-logo" style={{ width: '48px', height: '48px', fontSize: '1.5rem' }}>
            <FiLayers />
          </div>
        </div>
        <h2 style={{ textAlign: 'center', marginBottom: '2rem', fontSize: '1.75rem' }}>Welcome to DevFlow</h2>
        {error && <div className="badge danger" style={{ display: 'flex', justifyContent: 'center', marginBottom: '1.5rem' }}>{error}</div>}
        <form onSubmit={handleLogin}>
          <div className="input-group">
            <label>Username</label>
            <input type="text" value={username} onChange={e => setUsername(e.target.value)} />
          </div>
          <div className="input-group">
            <label>Password</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} />
          </div>
          <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '1rem' }}>
            Sign In to Console
          </button>
        </form>
      </div>
    </div>
  );
};

export const Sidebar = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const isActive = (path) => location.pathname === path ? 'active' : '';
  const user = JSON.parse(localStorage.getItem('user') || '{}');

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-logo"><FiLayers /></div>
        <h2>DevFlow</h2>
      </div>
      
      <Link to="/" className={isActive('/')}><FiLayout /> Dashboard</Link>
      <Link to="/projects" className={isActive('/projects')}><FiBox /> Projects</Link>
      <Link to="/deployments" className={isActive('/deployments')}><FiPlay /> Deployments</Link>
      <Link to="/clusters" className={isActive('/clusters')}><FiServer /> Clusters</Link>
      <Link to="/incidents" className={isActive('/incidents')}><FiAlertTriangle /> Incidents</Link>
      
      <div className="user-profile">
        <div className="user-avatar">{user.username ? user.username.charAt(0).toUpperCase() : 'U'}</div>
        <div className="user-info">
          <span className="user-name">{user.username}</span>
          <span className="user-role"><FiShield style={{display: 'inline', marginRight: '4px', verticalAlign: 'text-bottom'}}/>{user.role}</span>
        </div>
        <button onClick={handleLogout} style={{background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', marginLeft: 'auto', padding: '0.5rem'}}>
          <FiLogOut size={18} />
        </button>
      </div>
    </div>
  );
};

export const Dashboard = () => {
  const data = [
    { name: '10:00', cpu: 45, mem: 60 },
    { name: '10:05', cpu: 55, mem: 65 },
    { name: '10:10', cpu: 40, mem: 60 },
    { name: '10:15', cpu: 80, mem: 75 },
    { name: '10:20', cpu: 65, mem: 70 },
    { name: '10:25', cpu: 50, mem: 65 },
  ];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Platform Overview</h1>
          <p className="page-subtitle">Real-time metrics and system health at a glance.</p>
        </div>
      </div>

      <div className="grid-cards" style={{ marginBottom: '2.5rem' }}>
        <div className="glass-panel stat-card">
          <div className="stat-icon blue"><FiServer /></div>
          <div className="stat-content">
            <h3>Active Clusters</h3>
            <p>2</p>
          </div>
        </div>
        <div className="glass-panel stat-card">
          <div className="stat-icon green"><FiBox /></div>
          <div className="stat-content">
            <h3>Total Pods</h3>
            <p>48</p>
          </div>
        </div>
        <div className="glass-panel stat-card">
          <div className="stat-icon red"><FiAlertTriangle /></div>
          <div className="stat-content">
            <h3>Open Incidents</h3>
            <p>1</p>
          </div>
        </div>
      </div>
      
      <div className="glass-panel" style={{ height: '450px' }}>
        <h3 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <FiActivity /> Cluster Resource Usage (Avg)
        </h3>
        <ResponsiveContainer width="100%" height="90%">
          <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="colorCpu" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="colorMem" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
            <XAxis dataKey="name" stroke="#64748b" axisLine={false} tickLine={false} />
            <YAxis stroke="#64748b" axisLine={false} tickLine={false} />
            <RechartsTooltip 
              contentStyle={{ backgroundColor: 'rgba(15, 23, 42, 0.9)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', backdropFilter: 'blur(8px)' }}
              itemStyle={{ color: '#fff' }}
            />
            <Area type="monotone" dataKey="cpu" stroke="#3b82f6" strokeWidth={3} fillOpacity={1} fill="url(#colorCpu)" name="CPU %" />
            <Area type="monotone" dataKey="mem" stroke="#10b981" strokeWidth={3} fillOpacity={1} fill="url(#colorMem)" name="Memory %" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export const Projects = () => {
  const [projects, setProjects] = useState([]);

  useEffect(() => {
    axios.get(`${API_URL}/projects`).then(res => setProjects(res.data));
  }, []);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Projects</h1>
          <p className="page-subtitle">Manage connected repositories and services.</p>
        </div>
      </div>
      <div className="table-container glass-panel" style={{ padding: '0.5rem 1rem 1rem' }}>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Repository</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
            {projects.map(p => (
              <tr key={p.id}>
                <td style={{ color: 'var(--text-secondary)' }}>#{p.id}</td>
                <td><strong>{p.name}</strong></td>
                <td>
                  <a href={p.repository_url} target="_blank" rel="noreferrer" style={{color: 'var(--accent-color)', textDecoration: 'none'}}>
                    {p.repository_url}
                  </a>
                </td>
                <td style={{ color: 'var(--text-secondary)' }}>{p.description}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export const Deployments = () => {
  const [deployments, setDeployments] = useState([]);

  useEffect(() => {
    fetchDeployments();
  }, []);

  const fetchDeployments = () => {
    axios.get(`${API_URL}/deployments`).then(res => setDeployments(res.data));
  };

  const triggerDeploy = async (projectId) => {
    await axios.post(`${API_URL}/deployments`, { project_id: projectId, environment: 'prod' });
    fetchDeployments();
  };

  const rollbackDeploy = async (deployId) => {
    await axios.post(`${API_URL}/deployments/${deployId}/rollback`);
    fetchDeployments();
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Deployments</h1>
          <p className="page-subtitle">Track and orchestrate CI/CD pipelines.</p>
        </div>
        <button className="btn btn-primary" onClick={() => triggerDeploy(1)}>
          <FiPlay size={18} /> Deploy Payment GW
        </button>
      </div>
      
      <div className="table-container glass-panel" style={{ padding: '0.5rem 1rem 1rem' }}>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Project</th>
              <th>Env</th>
              <th>Status</th>
              <th>Deployed By</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {deployments.map(d => (
              <tr key={d.id}>
                <td style={{ color: 'var(--text-secondary)' }}>#{d.id}</td>
                <td><strong>Project {d.project_id}</strong></td>
                <td><span className="badge neutral">{d.environment}</span></td>
                <td>
                  <span className={`badge ${d.status}`}>
                    {d.status === 'success' && <FiCheckCircle size={14} />}
                    {d.status === 'failed' && <FiXCircle size={14} />}
                    {d.status === 'running' && <FiActivity size={14} />}
                    {d.status}
                  </span>
                </td>
                <td style={{ color: 'var(--text-secondary)' }}>{d.deployed_by}</td>
                <td>
                  {d.status === 'success' && (
                    <button className="btn btn-danger" style={{padding: '0.4rem 0.8rem', fontSize: '0.8rem'}} onClick={() => rollbackDeploy(d.id)}>
                      <FiRotateCcw size={14} /> Rollback
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export const Clusters = () => {
  const [clusters, setClusters] = useState([]);
  const [logs, setLogs] = useState([]);
  const [selectedCluster, setSelectedCluster] = useState(null);

  useEffect(() => {
    axios.get(`${API_URL}/clusters`).then(res => setClusters(res.data));
    const interval = setInterval(() => {
      axios.get(`${API_URL}/clusters`).then(res => setClusters(res.data));
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (!selectedCluster) return;
    const interval = setInterval(() => {
      axios.get(`${API_URL}/clusters/${selectedCluster}/logs`).then(res => {
        setLogs(prev => [...prev, ...res.data.logs].slice(-30)); // Keep last 30 logs
      });
    }, 3000);
    return () => clearInterval(interval);
  }, [selectedCluster]);

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
            onClick={() => setSelectedCluster(c.id)}
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
        <div className="glass-panel" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: '1.25rem 1.5rem', background: 'rgba(0,0,0,0.3)', borderBottom: '1px solid rgba(255,255,255,0.05)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FiTerminal /> <h3 style={{ margin: 0 }}>Live Logs: {clusters.find(c => c.id === selectedCluster)?.name}</h3>
          </div>
          <div className="terminal-window" style={{ border: 'none', borderRadius: 0, boxShadow: 'none' }}>
            {logs.length === 0 ? (
              <div style={{ color: 'var(--text-secondary)', fontStyle: 'italic' }}>Waiting for logs...</div>
            ) : (
              logs.map((log, i) => (
                <div key={i} className={`terminal-line ${log.includes('[ERROR]') ? 'terminal-error' : log.includes('[WARN]') ? 'terminal-warn' : 'terminal-info'}`}>
                  <span style={{ color: '#64748b' }}>[{new Date().toLocaleTimeString()}]</span> {log}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export const Incidents = () => {
  const [incidents, setIncidents] = useState([]);

  useEffect(() => {
    fetchIncidents();
  }, []);

  const fetchIncidents = () => {
    axios.get(`${API_URL}/incidents`).then(res => setIncidents(res.data));
  };

  const resolveIncident = async (id) => {
    await axios.patch(`${API_URL}/incidents/${id}`, { status: 'resolved' });
    fetchIncidents();
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Incidents</h1>
          <p className="page-subtitle">Track and resolve platform alerts.</p>
        </div>
      </div>
      <div className="table-container glass-panel" style={{ padding: '0.5rem 1rem 1rem' }}>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Title</th>
              <th>Severity</th>
              <th>Status</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {incidents.map(i => (
              <tr key={i.id}>
                <td style={{ color: 'var(--text-secondary)' }}>#{i.id}</td>
                <td><strong>{i.title}</strong></td>
                <td><span className={`badge ${i.severity}`}>{i.severity}</span></td>
                <td><span className={`badge ${i.status}`}>{i.status}</span></td>
                <td style={{ color: 'var(--text-secondary)' }}>{new Date(i.created_at).toLocaleString()}</td>
                <td>
                  {i.status !== 'resolved' && (
                    <button className="btn btn-success" style={{padding: '0.4rem 0.8rem', fontSize: '0.8rem'}} onClick={() => resolveIncident(i.id)}>
                      <FiCheckCircle size={14} /> Resolve
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
