import { Link, useLocation, useNavigate } from 'react-router-dom';
import { FiLayout, FiBox, FiServer, FiAlertTriangle, FiLogOut, FiLayers, FiShield, FiPlay, FiGithub, FiChevronDown, FiChevronUp, FiActivity, FiBell, FiSearch } from 'react-icons/fi';
import { useAuth } from '../../hooks/useAuth';
import { getInitials } from '../../utils/helpers';
import { useState } from 'react';

export function Sidebar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [githubOpen, setGithubOpen] = useState(location.pathname.startsWith('/github'));
  const [orchOpen, setOrchOpen] = useState(location.pathname.startsWith('/orchestration'));

  const isActive = (path) => location.pathname === path ? 'active' : '';
  const isGithubChild = (path) => location.pathname.startsWith(path) ? 'active' : '';
  const isOrchChild = (path) => location.pathname.startsWith(path) ? 'active' : '';

  const handleLogout = () => {
    logout();
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
      
      <div style={{ marginTop: '0.5rem' }}>
        <div className={`sidebar-section-header ${isOrchChild('/orchestration')}`}
          onClick={() => setOrchOpen(!orchOpen)}
          style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.75rem 1.25rem', color: orchOpen ? 'var(--text-primary)' : 'var(--text-secondary)', borderRadius: '12px', fontWeight: 600, fontSize: '0.95rem' }}>
          <FiActivity /> Orchestration
          <span style={{ marginLeft: 'auto' }}>{orchOpen ? <FiChevronUp size={16} /> : <FiChevronDown size={16} />}</span>
        </div>
        {orchOpen && (
          <div style={{ paddingLeft: '1rem' }}>
            <Link to="/orchestration" className={isActive('/orchestration')}>Dashboard</Link>
            <Link to="/orchestration/incidents" className={isOrchChild('/orchestration/incidents')}>Incidents</Link>
            <Link to="/orchestration/root-cause" className={isActive('/orchestration/root-cause')}>Root Cause</Link>
            <Link to="/orchestration/notifications" className={isActive('/orchestration/notifications')}>Notifications</Link>
          </div>
        )}
      </div>
      
      <div style={{ marginTop: '0.5rem' }}>
        <div className={`sidebar-section-header ${isGithubChild('/github')}`}
          onClick={() => setGithubOpen(!githubOpen)}
          style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.75rem 1.25rem', color: githubOpen ? 'var(--text-primary)' : 'var(--text-secondary)', borderRadius: '12px', fontWeight: 600, fontSize: '0.95rem' }}>
          <FiGithub /> GitHub
          <span style={{ marginLeft: 'auto' }}>{githubOpen ? <FiChevronUp size={16} /> : <FiChevronDown size={16} />}</span>
        </div>
        {githubOpen && (
          <div style={{ paddingLeft: '1rem' }}>
            <Link to="/github" className={isActive('/github')}>Connect</Link>
            <Link to="/github/repos" className={isActive('/github/repos')}>Repositories</Link>
          </div>
        )}
      </div>
      
      <div className="user-profile">
        <div className="user-avatar">{getInitials(user.username)}</div>
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
}
