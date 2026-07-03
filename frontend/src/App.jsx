import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { AppLayout } from './layouts/AppLayout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Projects from './pages/Projects';
import Deployments from './pages/Deployments';
import Clusters from './pages/Clusters';
import Incidents from './pages/Incidents';
import Github from './pages/Github';
import Repositories from './pages/Repositories';
import RepositoryDetail from './pages/RepositoryDetail';
import RepositoryDeployments from './pages/RepositoryDeployments';
import RepositorySettings from './pages/RepositorySettings';
import Commits from './pages/Commits';
import PullRequests from './pages/PullRequests';
import Branches from './pages/Branches';
import OrchestrationDashboard from './pages/OrchestrationDashboard';
import OrchestrationIncidents from './pages/OrchestrationIncidents';
import IncidentDetails from './pages/IncidentDetails';
import EvidenceViewer from './pages/EvidenceViewer';
import TimelineViewer from './pages/TimelineViewer';
import RootCauseAnalysis from './pages/RootCauseAnalysis';
import Notifications from './pages/Notifications';
import MonitoringDashboard from './pages/Monitoring';
import PrometheusMetrics from './pages/Monitoring/Metrics';
import GrafanaDashboards from './pages/Monitoring/Dashboards';
import ActiveAlerts from './pages/Monitoring/Alerts';

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<AppLayout><Dashboard /></AppLayout>} />
          <Route path="/projects" element={<AppLayout><Projects /></AppLayout>} />
          <Route path="/deployments" element={<AppLayout><Deployments /></AppLayout>} />
          <Route path="/clusters" element={<AppLayout><Clusters /></AppLayout>} />
          <Route path="/incidents" element={<AppLayout><Incidents /></AppLayout>} />
          <Route path="/orchestration" element={<AppLayout><OrchestrationDashboard /></AppLayout>} />
          <Route path="/orchestration/incidents" element={<AppLayout><OrchestrationIncidents /></AppLayout>} />
          <Route path="/orchestration/incidents/:incidentId" element={<AppLayout><IncidentDetails /></AppLayout>} />
          <Route path="/orchestration/evidence/:incidentId" element={<AppLayout><EvidenceViewer /></AppLayout>} />
          <Route path="/orchestration/timeline/:incidentId" element={<AppLayout><TimelineViewer /></AppLayout>} />
          <Route path="/orchestration/root-cause" element={<AppLayout><RootCauseAnalysis /></AppLayout>} />
          <Route path="/orchestration/notifications" element={<AppLayout><Notifications /></AppLayout>} />
          <Route path="/monitoring" element={<AppLayout><MonitoringDashboard /></AppLayout>} />
          <Route path="/monitoring/metrics" element={<AppLayout><PrometheusMetrics /></AppLayout>} />
          <Route path="/monitoring/dashboards" element={<AppLayout><GrafanaDashboards /></AppLayout>} />
          <Route path="/monitoring/alerts" element={<AppLayout><ActiveAlerts /></AppLayout>} />
          <Route path="/github" element={<AppLayout><Github /></AppLayout>} />
          <Route path="/github/repos" element={<AppLayout><Repositories /></AppLayout>} />
          <Route path="/github/repos/:repoId" element={<AppLayout><RepositoryDetail /></AppLayout>} />
          <Route path="/github/repos/:repoId/commits" element={<AppLayout><Commits /></AppLayout>} />
          <Route path="/github/repos/:repoId/pulls" element={<AppLayout><PullRequests /></AppLayout>} />
          <Route path="/github/repos/:repoId/branches" element={<AppLayout><Branches /></AppLayout>} />
          <Route path="/github/repos/:repoId/deployments" element={<AppLayout><RepositoryDeployments /></AppLayout>} />
          <Route path="/github/repos/:repoId/settings" element={<AppLayout><RepositorySettings /></AppLayout>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
