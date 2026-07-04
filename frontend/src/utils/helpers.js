export const formatDate = (dateStr) => {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return d.toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' });
};

export const formatDateShort = (dateStr) => {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-IN', { timeZone: 'Asia/Kolkata' });
};

export const formatTime = (dateStr) => {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return d.toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata' });
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
