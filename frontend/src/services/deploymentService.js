import api from './api';

export const getDeployments = async (params = {}) => {
  const res = await api.get('/deployments', { params });
  return res.data;
};

export const getDeployment = async (id) => {
  const res = await api.get(`/deployments/${id}`);
  return res.data;
};

export const createDeployment = async ({ project_id, branch, commit_sha, environment }) => {
  const res = await api.post('/deployments', { project_id, branch, commit_sha, environment });
  return res.data;
};

export const rollbackDeployment = async (deploymentId) => {
  const res = await api.post(`/deployments/${deploymentId}/rollback`);
  return res.data;
};

export const getRolloutStatus = async (deploymentId) => {
  const res = await api.get(`/deployments/${deploymentId}/rollout-status`);
  return res.data;
};
