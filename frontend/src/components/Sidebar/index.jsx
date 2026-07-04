import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  FiLayout, FiBox, FiGitBranch, FiGithub, FiServer, FiAlertTriangle,
  FiActivity, FiCpu, FiBarChart2, FiSettings, FiShield, FiLogOut,
  FiLayers, FiTerminal
} from 'react-icons/fi';
import { useAuth } from '../../hooks/useAuth';
import { getInitials } from '../../utils/helpers';

const NAV_SECTIONS = [
  {
    label: 'Command Center',
    items: [
      { path: '/', label: 'Dashboard', icon: FiLayout },
      { path: '/projects', label: 'Projects', icon: FiBox },
      { path: '/github/repos', label: 'Repositories', icon: FiGitBranch },
    ],
  },
  {
    label: 'Operations',
    items: [
      { path: '/deployments', label: 'Deployments', icon: FiTerminal },
      { path: '/orchestration/incidents', label: 'Incidents', icon: FiAlertTriangle },
      { path: '/orchestration/root-cause', label: 'AI Analysis', icon: FiActivity },
      { path: '/monitoring', label: 'Observability', icon: FiBarChart2 },
    ],
  },
  {
    label: 'Infrastructure',
    items: [
      { path: '/github', label: 'GitHub', icon: FiGithub },
      { path: '/clusters', label: 'Kubernetes', icon: FiServer },
      { path: '/monitoring/metrics', label: 'Metrics', icon: FiCpu },
    ],
  },
  {
    label: 'System',
    items: [
      { path: '/settings', label: 'Settings', icon: FiSettings },
    ],
  },
];

export function Sidebar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const isActive = (path) => {
    if (path === '/') return location.pathname === '/' ? 'active' : '';
    return location.pathname.startsWith(path) ? 'active' : '';
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-logo"><FiLayers /></div>
        <h2>DevFlow</h2>
      </div>

      {NAV_SECTIONS.map((section) => (
        <div key={section.label}>
          <div className="sidebar-section-label">{section.label}</div>
          {section.items.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`sidebar-link ${isActive(item.path)}`}
            >
              <item.icon />
              <span>{item.label}</span>
            </Link>
          ))}
        </div>
      ))}

      <div className="sidebar-footer">
        <div className="user-profile">
          <div className="user-avatar">{getInitials(user?.username || 'U')}</div>
          <div className="user-info">
            <span className="user-name">{user?.username || 'User'}</span>
            <span className="user-role">
              <FiShield size={10} style={{ display: 'inline', marginRight: 3, verticalAlign: 'middle' }} />
              {user?.role || 'admin'}
            </span>
          </div>
          <button className="logout-btn" onClick={handleLogout} title="Logout">
            <FiLogOut size={16} />
          </button>
        </div>
      </div>
    </nav>
  );
}
