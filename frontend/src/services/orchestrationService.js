import api from './api';

export const getOrchestrationDashboard = () =>
  api.get('/orchestration/dashboard').then(r => r.data);

export const getIncidents = (params = {}) =>
  api.get('/orchestration/incidents', { params }).then(r => r.data);

export const getIncident = (id) =>
  api.get(`/orchestration/incidents/${id}`).then(r => r.data);

export const resolveIncident = (id, notes = '') =>
  api.post(`/orchestration/incidents/${id}/resolve`, { notes }).then(r => r.data);

export const mergeIncidents = (primaryId, secondaryIds) =>
  api.post('/orchestration/incidents/merge', { primary_id: primaryId, secondary_ids: secondaryIds }).then(r => r.data);

export const ingestEvent = (eventType, metadata = {}) =>
  api.post('/orchestration/events', { event_type: eventType, metadata }).then(r => r.data);

export const getEventHistory = (params = {}) =>
  api.get('/orchestration/history', { params }).then(r => r.data);

export const getCollectors = () =>
  api.get('/orchestration/collectors').then(r => r.data);

export const getSeverityRules = () =>
  api.get('/orchestration/severity/rules').then(r => r.data);
