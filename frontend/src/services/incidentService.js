import api from './api';

export const getIncidents = async () => {
  const res = await api.get('/incidents');
  return res.data;
};

export const resolveIncident = async (incidentId) => {
  const res = await api.patch(`/incidents/${incidentId}`, { status: 'resolved' });
  return res.data;
};

export const createIncident = async (title, severity = 'medium') => {
  const res = await api.post('/incidents', { title, severity });
  return res.data;
};
