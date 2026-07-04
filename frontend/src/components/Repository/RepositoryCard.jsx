import { useNavigate } from 'react-router-dom';
import { FiStar, FiGitBranch, FiTrash2, FiExternalLink, FiLink, FiPlus, FiCpu } from 'react-icons/fi';

export function RepositoryCard({ repository, connected, onConnect, onDisconnect, disableNavigation }) {
  const navigate = useNavigate();

  const handleCardClick = () => {
    if (disableNavigation) return;
    if (connected) {
      const targetId = repository.project_id || repository.id;
      navigate(`/repositories/${targetId}`);
    }
  };

  return (
    <div className="glass-panel card-hover repo-card"
      key={repository.id}
      onClick={handleCardClick}
      style={{ cursor: disableNavigation ? 'default' : 'pointer' }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <h3 style={{ margin: 0, fontSize: '1rem', color: '#fff', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{repository.name}</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginTop: '0.2rem' }}>
            {repository.owner || repository.full_name?.split('/')[0]}
          </p>
        </div>
        <span className={`badge ${repository.visibility === 'private' ? 'neutral' : 'success'}`}>
          {repository.visibility}
        </span>
      </div>

      <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', flex: 1, marginBottom: '1rem', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
        {repository.description || 'No description'}
      </p>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', gap: '1rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
          {repository.language && <span>{repository.language}</span>}
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}><FiStar size={14} /> {repository.stars || repository.stargazers_count || 0}</span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}><FiGitBranch size={14} /> {repository.forks || repository.forks_count || 0}</span>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }} onClick={e => e.stopPropagation()}>
          <button className="btn btn-ghost btn-sm"
            onClick={() => window.open(repository.html_url, '_blank', 'noopener,noreferrer')}
            title="Open in GitHub">
            <FiExternalLink size={12} />
          </button>
          {connected ? (
            onDisconnect ? (
              <button className="btn btn-danger btn-sm"
                onClick={() => onDisconnect(repository.id)}>
                <FiTrash2 size={12} /> Disconnect
              </button>
            ) : (
              <span className="badge connected"><FiCpu size={10} /> Managed</span>
            )
          ) : onConnect ? (
            <button className="btn btn-primary btn-sm"
              onClick={() => onConnect(repository.owner || repository.full_name?.split('/')[0], repository.name)}>
              <FiPlus size={12} /> Connect
            </button>
          ) : (
            <button className="btn btn-primary btn-sm"
              onClick={() => navigate('/github/repos')}>
              <FiPlus size={12} /> Connect
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
