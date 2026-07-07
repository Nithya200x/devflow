import api from './api';

export const getPipelineRuns = async (projectId) => {
  const res = await api.get(`/pipelines/github/${projectId}/runs`);
  return res.data;
};

export const getLatestPipeline = async (projectId) => {
  const res = await api.get(`/pipelines/github/${projectId}/latest`);
  return res.data;
};

export const getPipelineJobs = async (projectId, runId) => {
  const res = await api.get(`/pipelines/github/${projectId}/runs/${runId}/jobs`);
  return res.data;
};
