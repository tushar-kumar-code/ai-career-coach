'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signInWithPopup,
  signOut,
  onAuthStateChanged,
  updateProfile,
  User as FirebaseUser,
} from 'firebase/auth';
import { auth, googleProvider } from '@/lib/firebase';
import { UserAuthData } from '@/lib/types';
import {
  getMe,
  getSavedAuthToken,
  saveAuthToken,
  clearAuthToken,
  demoLoginUser,
} from '@/lib/api-client';

interface AuthContextType {
  user: UserAuthData | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  hasCompletedAssessment: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  loginWithGoogle: () => Promise<void>;
  demoLogin: () => Promise<void>;
  logout: () => Promise<void>;
  markAssessmentCompleted: () => void;
  refreshUser: () => Promise<UserAuthData | undefined>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserAuthData | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  // Sync authenticated session with backend
  const syncWithBackend = async (idToken: string, fbUser?: FirebaseUser | null): Promise<UserAuthData | null> => {
    saveAuthToken(idToken);
    setToken(idToken);
    try {
      const backendUser = await getMe();
      setUser(backendUser);
      if (typeof window !== 'undefined') {
        localStorage.setItem('auth_user', JSON.stringify(backendUser));
      }
      return backendUser;
    } catch (err) {
      console.warn('Backend profile sync notice:', err);
      // Fallback user from Firebase credentials if backend is temporarily offline
      if (fbUser) {
        const fallbackUser: UserAuthData = {
          id: fbUser.uid,
          email: fbUser.email || '',
          full_name: fbUser.displayName || (fbUser.email ? fbUser.email.split('@')[0] : 'Candidate'),
          is_active: true,
          has_completed_assessment: false,
        };
        setUser(fallbackUser);
        return fallbackUser;
      }
      return null;
    }
  };

  useEffect(() => {
    let isMounted = true;

    // Load cached session for instantaneous UI responsiveness
    if (typeof window !== 'undefined') {
      const cachedToken = getSavedAuthToken();
      const cachedUserStr = localStorage.getItem('auth_user');
      if (cachedToken) setToken(cachedToken);
      if (cachedUserStr) {
        try {
          setUser(JSON.parse(cachedUserStr));
        } catch {}
      }
    }

    const unsubscribe = onAuthStateChanged(auth, async (fbUser) => {
      if (!isMounted) return;

      if (fbUser) {
        try {
          const idToken = await fbUser.getIdToken();
          if (isMounted) {
            await syncWithBackend(idToken, fbUser);
          }
        } catch (err) {
          console.error('Error fetching Firebase ID token:', err);
        }
      } else {
        // If not logged in via Firebase, check if there is an active backend/demo session
        const savedToken = getSavedAuthToken();
        if (savedToken) {
          try {
            const me = await getMe();
            if (isMounted) {
              setUser(me);
              setToken(savedToken);
            }
          } catch {
            clearAuthToken();
            if (isMounted) {
              setUser(null);
              setToken(null);
            }
          }
        } else {
          if (isMounted) {
            setUser(null);
            setToken(null);
          }
        }
      }

      if (isMounted) {
        setIsLoading(false);
      }
    });

    return () => {
      isMounted = false;
      unsubscribe();
    };
  }, []);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const cred = await signInWithEmailAndPassword(auth, email, password);
      const idToken = await cred.user.getIdToken();
      const syncedUser = await syncWithBackend(idToken, cred.user);
      if (syncedUser && !syncedUser.has_completed_assessment) {
        router.push('/assessment');
      } else {
        router.push('/dashboard');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (email: string, password: string, fullName?: string) => {
    setIsLoading(true);
    try {
      const cred = await createUserWithEmailAndPassword(auth, email, password);
      if (fullName && fullName.trim()) {
        try {
          await updateProfile(cred.user, { displayName: fullName.trim() });
        } catch (e) {
          console.warn('Profile name update notice:', e);
        }
      }
      const idToken = await cred.user.getIdToken();
      await syncWithBackend(idToken, cred.user);
      router.push('/assessment');
    } finally {
      setIsLoading(false);
    }
  };

  const loginWithGoogle = async () => {
    setIsLoading(true);
    try {
      const cred = await signInWithPopup(auth, googleProvider);
      const idToken = await cred.user.getIdToken();
      const syncedUser = await syncWithBackend(idToken, cred.user);
      if (syncedUser && !syncedUser.has_completed_assessment) {
        router.push('/assessment');
      } else {
        router.push('/dashboard');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const demoLogin = async () => {
    setIsLoading(true);
    try {
      const res = await demoLoginUser();
      setToken(res.access_token);
      saveAuthToken(res.access_token);
      setUser(res.user);
      if (typeof window !== 'undefined') {
        localStorage.setItem('auth_user', JSON.stringify(res.user));
      }
      if (!res.user.has_completed_assessment) {
        router.push('/assessment');
      } else {
        router.push('/dashboard');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      await signOut(auth);
    } catch (e) {
      console.warn('Sign out notice:', e);
    }
    clearAuthToken();
    setUser(null);
    setToken(null);
    router.push('/login');
  };

  const markAssessmentCompleted = () => {
    setUser((prev) => {
      if (!prev) return prev;
      const updated = { ...prev, has_completed_assessment: true };
      if (typeof window !== 'undefined') {
        localStorage.setItem('auth_user', JSON.stringify(updated));
      }
      return updated;
    });
  };

  const refreshUser = async () => {
    try {
      if (auth.currentUser) {
        const freshToken = await auth.currentUser.getIdToken(true);
        return (await syncWithBackend(freshToken, auth.currentUser)) || undefined;
      }
      const currentUser = await getMe();
      setUser(currentUser);
      if (typeof window !== 'undefined') {
        localStorage.setItem('auth_user', JSON.stringify(currentUser));
      }
      return currentUser;
    } catch {
      return undefined;
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user,
        isLoading,
        hasCompletedAssessment: !!user?.has_completed_assessment,
        login,
        register,
        loginWithGoogle,
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
