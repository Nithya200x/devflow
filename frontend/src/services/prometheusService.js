import api from './api';

export const getPrometheusHealth = () =>
  api.get('/prometheus/health').then(r => r.data);

export const queryPrometheus = (query) =>
  api.post('/prometheus/query', { query }).then(r => r.data);

export const queryRange = (query, start, end, step = '15s') =>
  api.post('/prometheus/query_range', { query, start, end, step }).then(r => r.data);

export const getCPUMetrics = (params = {}) =>
  api.get('/prometheus/metrics/cpu', { params }).then(r => r.data);

export const getMemoryMetrics = (params = {}) =>
  api.get('/prometheus/metrics/memory', { params }).then(r => r.data);

export const getDiskMetrics = (params = {}) =>
  api.get('/prometheus/metrics/disk', { params }).then(r => r.data);

export const getNetworkMetrics = (params = {}) =>
  api.get('/prometheus/metrics/network', { params }).then(r => r.data);

export const getPodMetrics = (params = {}) =>
  api.get('/prometheus/metrics/pod', { params }).then(r => r.data);

export const getNodeMetrics = (params = {}) =>
  api.get('/prometheus/metrics/node', { params }).then(r => r.data);

export const getDeploymentMetrics = (params = {}) =>
  api.get('/prometheus/metrics/deployment', { params }).then(r => r.data);

export const getServiceMetrics = (params = {}) =>
  api.get('/prometheus/metrics/service', { params }).then(r => r.data);

export const getErrorRate = (params = {}) =>
  api.get('/prometheus/metrics/error-rate', { params }).then(r => r.data);

export const getRequestRate = (params = {}) =>
  api.get('/prometheus/metrics/request-rate', { params }).then(r => r.data);

export const getLatency = (params = {}) =>
  api.get('/prometheus/metrics/latency', { params }).then(r => r.data);

export const getActiveAlerts = () =>
  api.get('/prometheus/alerts').then(r => r.data);
