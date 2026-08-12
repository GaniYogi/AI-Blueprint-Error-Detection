import React, { createContext, useContext, useState, useEffect } from 'react';
import { authService } from '../services/api';

interface AuthContextType {
  user: any;
  loading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<any>;
  register: (email: string, password: string, fullName: string) => Promise<any>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const DEFAULT_USER = {
  id: 1,
  email: 'architect@blueprint.ai',
  full_name: 'Architect User',
  is_active: true,
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<any>(() => {
    const savedUser = localStorage.getItem('user');
    if (savedUser) {
      try {
        return JSON.parse(savedUser);
      } catch (e) {
        console.error(e);
      }
    }
    return DEFAULT_USER;
  });

  const [loading, setLoading] = useState<boolean>(true);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(true);

  const refreshUser = async () => {
    try {
      const me = await authService.getMe();
      if (me) {
        setUser(me);
        setIsAuthenticated(true);
        localStorage.setItem('user', JSON.stringify(me));
      }
    } catch (err) {
      console.warn('Backend user status sync:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshUser();
  }, []);

  const login = async (email: string, password: string) => {
    setLoading(true);
    try {
      const data = await authService.login(email, password);
      if (data && data.access_token) {
        localStorage.setItem('token', data.access_token);
        setUser(data.user);
        setIsAuthenticated(true);
        localStorage.setItem('user', JSON.stringify(data.user));
      }
      return data;
    } finally {
      setLoading(false);
    }
  };

  const register = async (email: string, password: string, fullName: string) => {
    setLoading(true);
    try {
      await authService.register({ email, password, full_name: fullName });
      return await login(email, password);
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(DEFAULT_USER);
    setIsAuthenticated(true);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated,
        login,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
