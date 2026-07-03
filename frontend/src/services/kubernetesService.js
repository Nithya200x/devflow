import api from './api';

export const getKubernetesHealth = () =>
  api.get('/kubernetes/health').then(r => r.data);

export const listPods = (params = {}) =>
  api.get('/kubernetes/pods', { params }).then(r => r.data);

export const getPod = (namespace, name) =>
  api.get(`/kubernetes/pods/${namespace}/${name}`).then(r => r.data);

export const getPodLogs = (namespace, name, params = {}) =>
  api.get(`/kubernetes/pods/${namespace}/${name}/logs`, { params }).then(r => r.data);

export const listDeployments = (params = {}) =>
  api.get('/kubernetes/deployments', { params }).then(r => r.data);

export const getDeployment = (namespace, name) =>
  api.get(`/kubernetes/deployments/${namespace}/${name}`).then(r => r.data);

export const listNodes = () =>
  api.get('/kubernetes/nodes').then(r => r.data);

export const listNamespaces = () =>
  api.get('/kubernetes/namespaces').then(r => r.data);

export const listKubernetesEvents = (params = {}) =>
  api.get('/kubernetes/events', { params }).then(r => r.data);

export const listServices = (params = {}) =>
  api.get('/kubernetes/services', { params }).then(r => r.data);

export const listIngresses = (params = {}) =>
  api.get('/kubernetes/ingresses', { params }).then(r => r.data);

export const getClusterMetrics = () =>
  api.get('/kubernetes/metrics').then(r => r.data);
