import api from './api';

export const login = async (username, password) => {
  const res = await api.post('/auth/login', { username, password });
  return res.data;
};

export const register = async ({ name, email, username, password }) => {
  const res = await api.post('/auth/register', { name, email, username, password });
  return res.data;
};
