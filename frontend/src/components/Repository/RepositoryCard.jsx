import { useNavigate } from 'react-router-dom';
import { FiStar, FiGitBranch, FiTrash2, FiExternalLink, FiLink, FiPlus } from 'react-icons/fi';

export function RepositoryCard({ repository, connected, onConnect, onDisconnect, disableNavigation }) {
  const navigate = useNavigate();

  const handleCardClick = () => {
    if (!disableNavigation && repository.id) {
      navigate(`/github/repos/${repository.id}`);
    }
  };

  return (
    <div className="glass-panel repo-card" key={repository.id} style={{ cursor: 'pointer' }}
      onClick={handleCardClick}>
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
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}><FiStar size={14} /> {repository.stars}</span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}><FiGitBranch size={14} /> {repository.forks}</span>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }} onClick={e => e.stopPropagation()}>
          <button className="btn btn-ghost" style={{ padding: '0.3rem 0.5rem', fontSize: '0.7rem' }}
            onClick={() => window.open(repository.html_url, '_blank', 'noopener,noreferrer')}
            title="Open in GitHub">
            <FiExternalLink size={12} />
          </button>
          {onDisconnect ? (
            <button className="btn btn-danger" style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}
              onClick={() => onDisconnect(repository.id)}>
              <FiTrash2 size={12} /> Disconnect
            </button>
          ) : connected ? (
            <span className="badge success"><FiLink size={12} /> Connected</span>
          ) : onConnect ? (
            <button className="btn btn-primary" style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}
              onClick={() => onConnect(repository.owner || repository.full_name?.split('/')[0], repository.name)}>
              <FiPlus size={12} /> Connect
            </button>
          ) : null}
        </div>
      </div>
    </div>
  );
}
