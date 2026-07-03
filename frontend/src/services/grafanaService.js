import api from './api';

export const getGrafanaHealth = () =>
  api.get('/grafana/health').then(r => r.data);

export const listDashboards = () =>
  api.get('/grafana/dashboards').then(r => r.data);

export const getDashboard = (uid) =>
  api.get(`/grafana/dashboards/${uid}`).then(r => r.data);

export const getDashboardByName = (name) =>
  api.get(`/grafana/dashboards/by-name/${encodeURIComponent(name)}`).then(r => r.data);

export const listDatasources = () =>
  api.get('/grafana/datasources').then(r => r.data);
