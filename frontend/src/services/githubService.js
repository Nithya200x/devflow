import api from './api';

export const getGitHubStatus = async () => {
  const res = await api.get('/github/status');
  return res.data;
};

export const connectGitHub = async (token) => {
  const res = await api.post('/github/connect', { token });
  return res.data;
};

export const disconnectGitHub = async () => {
  const res = await api.delete('/github/disconnect');
  return res.data;
};

export const getGitHubRepos = async () => {
  const res = await api.get('/github/repos');
  return res.data;
};

export const getConnectedRepos = async () => {
  const res = await api.get('/github/repositories');
  return res.data;
};

export const connectRepo = async (owner, name) => {
  const res = await api.post('/github/repositories', { owner, name });
  return res.data;
};

export const disconnectRepo = async (repoId) => {
  const res = await api.delete(`/github/repositories/${repoId}`);
  return res.data;
};

export const getRepoDetails = async (repoId) => {
  const res = await api.get(`/github/repositories/${repoId}/details`);
  return res.data;
};

export const getRepoCommits = async (repoId, branch) => {
  const params = branch ? `?branch=${branch}` : '';
  const res = await api.get(`/github/repositories/${repoId}/commits${params}`);
  return res.data;
};

export const getRepoBranches = async (repoId) => {
  const res = await api.get(`/github/repositories/${repoId}/branches`);
  return res.data;
};

export const getRepoPulls = async (repoId, state) => {
  const params = state ? `?state=${state}` : '';
  const res = await api.get(`/github/repositories/${repoId}/pulls${params}`);
  return res.data;
};

export const getRepoContributors = async (repoId) => {
  const res = await api.get(`/github/repositories/${repoId}/contributors`);
  return res.data;
};

export const getGitHubDashboard = async () => {
  const res = await api.get('/github/dashboard');
  return res.data;
};
