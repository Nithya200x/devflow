import api from './api';

export const getDeployments = async () => {
  const res = await api.get('/deployments');
  return res.data;
};

export const createDeployment = async (projectId, environment = 'prod') => {
  const res = await api.post('/deployments', { project_id: projectId, environment });
  return res.data;
};

export const rollbackDeployment = async (deploymentId) => {
  const res = await api.post(`/deployments/${deploymentId}/rollback`);
  return res.data;
};
