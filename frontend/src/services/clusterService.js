import api from './api';

export const getClusters = async () => {
  const res = await api.get('/clusters');
  return res.data;
};

export const getClusterLogs = async (clusterId) => {
  const res = await api.get(`/clusters/${clusterId}/logs`);
  return res.data;
};
