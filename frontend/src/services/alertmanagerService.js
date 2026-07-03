import api from './api';

export const getAlertmanagerHealth = () =>
  api.get('/alertmanager/health').then(r => r.data);

export const getAlerts = (params = {}) =>
  api.get('/alertmanager/alerts', { params }).then(r => r.data);

export const getSilences = () =>
  api.get('/alertmanager/silences').then(r => r.data);
