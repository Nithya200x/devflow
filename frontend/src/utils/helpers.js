export const formatDate = (dateStr) => {
  if (!dateStr) return '';
  return new Date(dateStr).toLocaleString();
};

export const getInitials = (username) => {
  return username ? username.charAt(0).toUpperCase() : 'U';
};

export const getUserFromStorage = () => {
  try {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : {};
  } catch {
    return {};
  }
};

export const getTokenFromStorage = () => {
  return localStorage.getItem('token');
};

export const clearAuthStorage = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
};
