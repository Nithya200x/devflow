import api from './api';

export const getAnalyticsDashboard = (days = 7) =>
  api.get('/analytics/dashboard', { params: { days } }).then(r => r.data);
