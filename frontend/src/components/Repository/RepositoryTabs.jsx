import { Link, useLocation } from 'react-router-dom';
import { FiBookOpen, FiGitBranch, FiGitPullRequest, FiLayers, FiSettings } from 'react-icons/fi';

export function RepositoryTabs({ repoId, basePath = `/github/repos/${repoId}` }) {
  const location = useLocation();

  const tabs = [
    { path: basePath, label: 'Overview', icon: FiBookOpen },
    { path: `${basePath}/commits`, label: 'Commits', icon: FiLayers },
    { path: `${basePath}/branches`, label: 'Branches', icon: FiGitBranch },
    { path: `${basePath}/pulls`, label: 'Pull Requests', icon: FiGitPullRequest },
    { path: `${basePath}/deployments`, label: 'Deployments', icon: FiLayers },
    { path: `${basePath}/settings`, label: 'Settings', icon: FiSettings },
  ];

  const isActive = (tabPath) => {
    if (tabPath === basePath) {
      return location.pathname === basePath;
    }
    return location.pathname.startsWith(tabPath);
  };

  return (
    <div className="repo-tabs">
      {tabs.map(tab => (
        <Link
          key={tab.path}
          to={tab.path}
          className={`repo-tab ${isActive(tab.path) ? 'active' : ''}`}
        >
          <tab.icon size={16} />
          <span>{tab.label}</span>
        </Link>
      ))}
    </div>
  );
}
