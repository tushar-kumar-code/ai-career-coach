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
  hasCompletedAssessment: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  demoLogin: () => Promise<void>;
  logout: () => void;
  markAssessmentCompleted: () => void;
  refreshUser: () => Promise<UserAuthData | undefined>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserAuthData | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    let isMounted = true;
    const initAuth = async () => {
      const savedToken = getSavedAuthToken();
      if (!savedToken) {
        if (isMounted) {
          setUser(null);
          setToken(null);
          setIsLoading(false);
        }
        return;
      }

      if (isMounted) setToken(savedToken);
      try {
        // Try cached user first for instantaneous UI render
        const cachedUserStr = localStorage.getItem('auth_user');
        if (cachedUserStr && isMounted) {
          try {
            setUser(JSON.parse(cachedUserStr));
          } catch {}
        }

        // Verify with backend with 3.5s timeout
        const fetchPromise = getMe();
        const timeoutPromise = new Promise<never>((_, reject) =>
          setTimeout(() => reject(new Error('Auth verification timeout')), 3500)
        );
        const currentUser = await Promise.race([fetchPromise, timeoutPromise]);
        if (isMounted) {
          setUser(currentUser);
          localStorage.setItem('auth_user', JSON.stringify(currentUser));
        }
      } catch (err) {
        console.warn('Session verification notice:', err);
        const cachedUserStr = localStorage.getItem('auth_user');
        if (!cachedUserStr && isMounted) {
          clearAuthToken();
          setUser(null);
          setToken(null);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    initAuth();
    return () => {
      isMounted = false;
    };
  }, []);

  const markAssessmentCompleted = () => {
    setUser((prev) => {
      if (!prev) return prev;
      const updated = { ...prev, has_completed_assessment: true };
      localStorage.setItem('auth_user', JSON.stringify(updated));
      return updated;
    });
  };

  const refreshUser = async () => {
    try {
      const currentUser = await getMe();
      setUser(currentUser);
      localStorage.setItem('auth_user', JSON.stringify(currentUser));
      return currentUser;
    } catch {
      return undefined;
    }
  };

  const login = async (email: string, password: string) => {
    const res = await loginUser(email, password);
    setToken(res.access_token);
    setUser(res.user);
    if (!res.user.has_completed_assessment) {
      router.push('/assessment');
    } else {
      router.push('/dashboard');
    }
  };

  const register = async (email: string, password: string, fullName?: string) => {
    const res = await registerUser(email, password, fullName);
    setToken(res.access_token);
    setUser(res.user);
    router.push('/assessment');
  };

  const demoLogin = async () => {
    const res = await demoLoginUser();
    setToken(res.access_token);
    setUser(res.user);
    if (!res.user.has_completed_assessment) {
      router.push('/assessment');
    } else {
      router.push('/dashboard');
    }
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
        hasCompletedAssessment: !!user?.has_completed_assessment,
        login,
        register,
        demoLogin,
        logout,
        markAssessmentCompleted,
        refreshUser,
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
