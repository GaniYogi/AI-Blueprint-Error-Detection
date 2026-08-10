import React, { createContext, useContext } from 'react';

interface AuthContextType {
  user: any;
  loading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

// Static default user — no login required
const DEFAULT_USER = {
  id: 1,
  email: 'architect@blueprint.ai',
  full_name: 'Architect User',
  is_active: true,
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Always authenticated, never loading
  const login = async () => {};
  const register = async () => {};
  const logout = () => {};
  const refreshUser = async () => {};

  return (
    <AuthContext.Provider
      value={{
        user: DEFAULT_USER,
        loading: false,
        isAuthenticated: true,
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
