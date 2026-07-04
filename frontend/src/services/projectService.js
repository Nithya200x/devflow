import api from './api';

export const getProjects = async () => {
  const res = await api.get('/projects');
  return res.data;
};

export const getProjectOverview = async (projectId) => {
  const res = await api.get(`/projects/${projectId}/overview`);
  return res.data;
};

export const getProjectTimeline = async (projectId) => {
  const res = await api.get(`/projects/${projectId}/timeline`);
  return res.data;
};

export const getProjectHealth = async (projectId) => {
  const res = await api.get(`/projects/${projectId}/health`);
  return res.data;
};
