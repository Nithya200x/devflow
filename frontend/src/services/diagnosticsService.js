import api from './api';

export const runDiagnostics = () =>
  api.get('/diagnostics').then(r => r.data);
