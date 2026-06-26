export const ROUTES = {
  LOGIN: '/login',
  DASHBOARD: '/',
  PROJECTS: '/projects',
  DEPLOYMENTS: '/deployments',
  CLUSTERS: '/clusters',
  INCIDENTS: '/incidents',
  GITHUB: '/github',
  ORCHESTRATION: '/orchestration',
  ORCHESTRATION_INCIDENTS: '/orchestration/incidents',
  ORCHESTRATION_ROOT_CAUSE: '/orchestration/root-cause',
  ORCHESTRATION_NOTIFICATIONS: '/orchestration/notifications',
};

export const DEPLOYMENT_STATUS = {
  RUNNING: 'running',
  SUCCESS: 'success',
  FAILED: 'failed',
};

export const INCIDENT_STATUS = {
  OPEN: 'open',
  INVESTIGATING: 'investigating',
  RESOLVED: 'resolved',
};

export const INCIDENT_SEVERITY = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
  CRITICAL: 'critical',
};

export const CLUSTER_STATUS = {
  ACTIVE: 'active',
  DEGRADED: 'degraded',
  OFFLINE: 'offline',
};
