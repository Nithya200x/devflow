import api from './api';

export const triggerBuild = async ({ repository, branch, commit_sha, triggered_by } = {}) => {
  const res = await api.post('/jenkins/build', { repository, branch, commit_sha, triggered_by });
  return res.data;
};

export const getQueueStatus = async (queueId) => {
  const res = await api.get(`/jenkins/queue/${queueId}`);
  return res.data;
};

export const getBuildStatus = async (buildNumber) => {
  const res = await api.get(`/jenkins/build/${buildNumber}`);
  return res.data;
};

export const getConsoleOutput = async (buildNumber) => {
  const res = await api.get(`/jenkins/build/${buildNumber}/console`);
  return res.data;
};

export const emitBuildEvent = async (buildNumber, { event_type, repository, branch, commit_sha, triggered_by } = {}) => {
  const res = await api.post(`/jenkins/build/${buildNumber}/event`, { event_type, repository, branch, commit_sha, triggered_by });
  return res.data;
};

export const getBuildHistory = async (limit = 50) => {
  const res = await api.get(`/jenkins/builds?limit=${limit}`);
  return res.data;
};

export const getJenkinsHealth = async () => {
  const res = await api.get('/jenkins/health');
  return res.data;
};
