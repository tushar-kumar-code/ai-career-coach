'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { UserAuthData } from '@/lib/types';
import {
  loginUser,
  registerUser,
  demoLoginUser,
  getMe,
  getSavedAuthToken,
  clearAuthToken,
} from '@/lib/api-client';

interface AuthContextType {
  user: UserAuthData | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  demoLogin: () => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserAuthData | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    const initAuth = async () => {
      const savedToken = getSavedAuthToken();
      if (!savedToken) {
        setUser(null);
        setToken(null);
        setIsLoading(false);
        return;
      }

      setToken(savedToken);
      try {
        // Try cached user first for instantaneous UI render
        const cachedUserStr = localStorage.getItem('auth_user');
        if (cachedUserStr) {
          try {
            setUser(JSON.parse(cachedUserStr));
          } catch {}
        }
        // Verify with backend
        const currentUser = await getMe();
        setUser(currentUser);
        localStorage.setItem('auth_user', JSON.stringify(currentUser));
      } catch (err) {
        console.warn('Session verification failed, clearing token:', err);
        clearAuthToken();
        setUser(null);
        setToken(null);
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  const login = async (email: string, password: string) => {
    const res = await loginUser(email, password);
    setToken(res.access_token);
    setUser(res.user);
    router.push('/dashboard');
  };

  const register = async (email: string, password: string, fullName?: string) => {
    const res = await registerUser(email, password, fullName);
    setToken(res.access_token);
    setUser(res.user);
    router.push('/dashboard');
  };

  const demoLogin = async () => {
    const res = await demoLoginUser();
    setToken(res.access_token);
    setUser(res.user);
    router.push('/dashboard');
  };

  const logout = () => {
    clearAuthToken();
    setUser(null);
    setToken(null);
    router.push('/login');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user && !!token,
        isLoading,
        login,
        register,
        demoLogin,
        logout,
      }}
    >
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
