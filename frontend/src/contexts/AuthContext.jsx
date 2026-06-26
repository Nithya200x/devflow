import { createContext, useState, useCallback, useEffect } from 'react';
import { clearAuthStorage, getTokenFromStorage, getUserFromStorage } from '../utils/helpers';

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(getUserFromStorage);
  const [token, setToken] = useState(getTokenFromStorage);
  const [isAuthenticated, setIsAuthenticated] = useState(!!token);

  useEffect(() => {
    setIsAuthenticated(!!token);
  }, [token]);

  const saveAuth = useCallback((accessToken, userData) => {
    localStorage.setItem('token', accessToken);
    localStorage.setItem('user', JSON.stringify(userData));
    setToken(accessToken);
    setUser(userData);
  }, []);

  const logout = useCallback(() => {
    clearAuthStorage();
    setToken(null);
    setUser({});
  }, []);

  return (
    <AuthContext.Provider value={{ user, token, isAuthenticated, saveAuth, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
