const config = {
  API_URL: import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api/v1',
  GRAFANA_DASHBOARD_URL: import.meta.env.VITE_GRAFANA_DASHBOARD_URL || '',
};

export default config;
