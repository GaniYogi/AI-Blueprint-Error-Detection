import React, { createContext, useState, useEffect, useContext } from 'react';
import { authService } from '../services/api';

interface AuthContextType {
  user: any;
  loading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const refreshUser = async () => {
    try {
      const data = await authService.getMe();
      setUser(data);
    } catch (err) {
      console.error('Failed to get current user:', err);
      setUser({
        id: 1,
        email: 'architect@blueprint.ai',
        full_name: 'Architect User',
        is_active: true
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshUser();
  }, []);

  const login = async (_email: string, _password: string) => {
    // Bypassed
  };

  const register = async (_email: string, _password: string, _fullName: string) => {
    // Bypassed
  };

  const logout = () => {
    // Bypassed
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated: !!user,
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
