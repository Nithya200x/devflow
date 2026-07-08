import api from './api';

export const getAlertmanagerHealth = () =>
  api.get('/alertmanager/health').then(r => r.data);

export const getAlerts = (params = {}) =>
  api.get('/alertmanager/alerts', { params }).then(r => r.data);

export const getAlertHistory = (params = {}) =>
  api.get('/alertmanager/alerts/history', { params }).then(r => r.data);

export const getAlertStats = () =>
  api.get('/alertmanager/alerts/stats').then(r => r.data);

export const getAlertDetail = (fingerprint) =>
  api.get(`/alertmanager/alerts/${fingerprint}`).then(r => r.data);

export const getSilences = () =>
  api.get('/alertmanager/silences').then(r => r.data);

export const createSilence = (data) =>
  api.post('/alertmanager/silences', data).then(r => r.data);

export const expireSilence = (silenceId) =>
  api.delete(`/alertmanager/silences/${silenceId}`).then(r => r.data);

export const getNotificationConfig = () =>
  api.get('/alertmanager/notifications').then(r => r.data);
