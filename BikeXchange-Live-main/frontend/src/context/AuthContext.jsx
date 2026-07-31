/**
 * Authentication context provider.
 * Manages user state, login/logout, and JWT tokens.
 */

import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Load user from localStorage on mount
  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    const token = localStorage.getItem('access_token');

    if (storedUser && token) {
      try {
        setUser(JSON.parse(storedUser));
      } catch (e) {
        api.clearTokens();
      }
    }
    setLoading(false);
  }, []);

  const login = useCallback(async (email, password) => {
    const data = await api.login(email, password);
    if (data?.user) {
      setUser(data.user);
    } else if (data?.access) {
      // Fetch profile if not included
      const profile = await api.getProfile();
      setUser(profile);
      localStorage.setItem('user', JSON.stringify(profile));
    }
    return data;
  }, []);

  const register = useCallback(async (userData) => {
    const data = await api.register(userData);
    if (data?.user) {
      setUser(data.user);
    }
    return data;
  }, []);

  const logout = useCallback(() => {
    api.clearTokens();
    setUser(null);
  }, []);

  const refreshUser = useCallback(async () => {
    try {
      const profile = await api.getProfile();
      setUser(profile);
      localStorage.setItem('user', JSON.stringify(profile));
    } catch (e) {
      // Token expired
      logout();
    }
  }, [logout]);

  const value = {
    user,
    loading,
    isAuthenticated: !!user,
    isAdmin: user?.role === 'ADMIN',
    login,
    register,
    logout,
    refreshUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext;
