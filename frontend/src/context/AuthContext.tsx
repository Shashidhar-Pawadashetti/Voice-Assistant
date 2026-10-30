import React, { createContext, useContext, useEffect, useState } from 'react';
import { FarmerResponse, LoginRequest, RegisterRequest } from '../types/auth';
import { authService } from '../services/auth';
import { revokeAudioBlobUrls } from '../services/audio';

interface AuthContextType {
  farmer: FarmerResponse | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (payload: LoginRequest) => Promise<void>;
  register: (payload: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [farmer, setFarmer] = useState<FarmerResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    // Attempt session restoration on page load
    authService.restoreSession()
      .then((f) => setFarmer(f))
      .finally(() => setIsLoading(false));
  }, []);

  const login = async (payload: LoginRequest) => {
    await authService.login(payload);
    const profile = await authService.getMe();
    setFarmer(profile);
  };

  const register = async (payload: RegisterRequest) => {
    const res = await authService.register(payload);
    setFarmer(res.farmer);
  };

  const logout = async () => {
    try {
      await authService.logout();
    } catch {
      // Guaranteed cleanup even if server request encounters offline network
    } finally {
      revokeAudioBlobUrls();
      setFarmer(null);
    }
  };

  const refreshProfile = async () => {
    if (farmer) {
      const updated = await authService.getMe();
      setFarmer(updated);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        farmer,
        isAuthenticated: !!farmer,
        isLoading,
        login,
        register,
        logout,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
};
