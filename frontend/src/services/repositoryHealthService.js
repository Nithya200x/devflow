import api from './api';

export const getHealthScore = (projectId) =>
  api.get(`/health/score/${projectId}`).then(r => r.data);

export const listHealthScores = () =>
  api.get('/health/score').then(r => r.data);

export const invalidateHealthCache = (projectId) =>
  api.post('/health/score/invalidate', { project_id: projectId }).then(r => r.data);
