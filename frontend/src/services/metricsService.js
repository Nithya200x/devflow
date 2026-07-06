import api from './api';

export const getMetricsSummary = () =>
  api.get('/metrics/summary').then(r => r.data);
