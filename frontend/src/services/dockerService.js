import api from './api';

export const getDockerHealth = () =>
  api.get('/docker/health').then(r => r.data);

export const listContainers = (params = {}) =>
  api.get('/docker/containers', { params }).then(r => r.data);

export const getContainer = (id) =>
  api.get(`/docker/containers/${id}`).then(r => r.data);

export const getContainerLogs = (id, tail = 100) =>
  api.get(`/docker/containers/${id}/logs`, { params: { tail } }).then(r => r.data);

export const getContainerStats = (id) =>
  api.get(`/docker/containers/${id}/stats`).then(r => r.data);

export const getAllStats = () =>
  api.get('/docker/stats').then(r => r.data);
