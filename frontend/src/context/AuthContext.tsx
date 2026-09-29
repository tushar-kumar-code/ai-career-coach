'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { UserAuthData } from '@/lib/types';
import {
  loginUser,
  registerUser,
  demoLoginUser,
  getMe,
  getSavedAuthToken,
  saveAuthToken,
  clearAuthToken,
  notifyLoginEvent,
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

  // Restore session from localStorage on initial load
  useEffect(() => {
    const restoreSession = async () => {
      if (typeof window === 'undefined') {
        setIsLoading(false);
        return;
      }

      const savedToken = getSavedAuthToken();
      const cachedUserStr = localStorage.getItem('auth_user');

      if (savedToken) {
        setToken(savedToken);
        // Load cached user immediately for instant UI responsiveness
        if (cachedUserStr) {
          try {
            const parsed = JSON.parse(cachedUserStr);
            if (parsed && parsed.email && parsed.email !== 'user@aicareercoach.ai') {
              setUser(parsed);
            } else {
              localStorage.removeItem('auth_user');
            }
          } catch {}
        }

        // Validate token with backend in the background
        try {
          const me = await getMe();
          if (me.email === 'user@aicareercoach.ai') {
            const { auth } = await import('@/lib/firebase');
            if (auth?.currentUser?.email) {
              me.email = auth.currentUser.email;
              me.full_name = auth.currentUser.displayName || auth.currentUser.email.split('@')[0];
            }
          }
          setUser(me);
          localStorage.setItem('auth_user', JSON.stringify(me));
        } catch {
          // Token is invalid/expired — clear it
          clearAuthToken();
          setUser(null);
          setToken(null);
        }
      } else {
        setUser(null);
        setToken(null);
      }

      setIsLoading(false);
    };

    restoreSession();
  }, []);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      // 1. Authenticate with backend
      const res = await loginUser(email, password);
      let activeToken = res.access_token;

      // 2. Also authenticate / sync with Firebase Auth if configured
      try {
        const { auth, isFirebaseConfigured } = await import('@/lib/firebase');
        if (isFirebaseConfigured && auth) {
          const { signInWithEmailAndPassword, createUserWithEmailAndPassword } = await import('firebase/auth');
          try {
            const cred = await signInWithEmailAndPassword(auth, email, password);
            const fbToken = await cred.user.getIdToken();
            activeToken = fbToken;
          } catch (fbSignInErr: any) {
            // If user exists in backend but not yet created in Firebase Auth, create in Firebase seamlessly
            const code = fbSignInErr.code || '';
            if (code === 'auth/user-not-found' || code === 'auth/invalid-credential') {
              try {
                const newCred = await createUserWithEmailAndPassword(auth, email, password);
                const fbToken = await newCred.user.getIdToken();
                activeToken = fbToken;
              } catch {}
            }
          }
        }
      } catch {}

      saveAuthToken(activeToken);
      setToken(activeToken);
      setUser(res.user);

      // Trigger background login success notification
      notifyLoginEvent();

      if (res.user.has_completed_assessment) {
        router.push('/dashboard');
      } else {
        router.push('/assessment');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (email: string, password: string, fullName?: string) => {
    setIsLoading(true);
    try {
      // 1. Sync registration with Firebase Auth if configured
      let firebaseToken: string | null = null;
      try {
        const { auth, isFirebaseConfigured } = await import('@/lib/firebase');
        if (isFirebaseConfigured && auth) {
          const { createUserWithEmailAndPassword, updateProfile } = await import('firebase/auth');
          try {
            const cred = await createUserWithEmailAndPassword(auth, email, password);
            if (fullName && cred.user) {
              await updateProfile(cred.user, { displayName: fullName });
            }
            firebaseToken = await cred.user.getIdToken();
          } catch (fbErr: any) {
            console.warn('Firebase user creation note:', fbErr.message);
          }
        }
      } catch {}

      // 2. Register in backend database
      const res = await registerUser(email, password, fullName);
      const activeToken = firebaseToken || res.access_token;
      saveAuthToken(activeToken);
      setToken(activeToken);
      setUser(res.user);
      router.push('/assessment');
    } finally {
      setIsLoading(false);
    }
  };

  // Google OAuth — uses Firebase only if credentials are configured
  const loginWithGoogle = async () => {
    setIsLoading(true);
    try {
      const { auth, googleProvider, isFirebaseConfigured } = await import('@/lib/firebase');
      if (!isFirebaseConfigured) {
        throw new Error(
          'Google sign-in is not configured yet: Firebase Web App credentials are missing. Please configure NEXT_PUBLIC_FIREBASE_API_KEY in frontend/.env.local or use Email/Password / Quick Demo Access.'
        );
      }
      const { signInWithPopup } = await import('firebase/auth');
      const cred = await signInWithPopup(auth, googleProvider);
      const idToken = await cred.user.getIdToken();

      // Save Firebase token and use it as the auth bearer
      saveAuthToken(idToken);
      setToken(idToken);

      // Trigger background login success notification email
      notifyLoginEvent();

      // Try to get user from backend using Firebase JWT
      try {
        const me = await getMe();
        if (!me.email || me.email === 'user@aicareercoach.ai') {
          me.email = cred.user.email || me.email;
          me.full_name = cred.user.displayName || cred.user.email?.split('@')[0] || me.full_name;
        }
        setUser(me);
        localStorage.setItem('auth_user', JSON.stringify(me));
        if (me.has_completed_assessment) {
          router.push('/dashboard');
        } else {
          router.push('/assessment');
        }
      } catch {
        // Backend doesn't know this user yet — create a minimal fallback profile
        const fallbackUser: UserAuthData = {
          id: cred.user.uid,
          email: cred.user.email || '',
          full_name: cred.user.displayName || cred.user.email?.split('@')[0] || 'Candidate',
          is_active: true,
          has_completed_assessment: false,
        };
        setUser(fallbackUser);
        localStorage.setItem('auth_user', JSON.stringify(fallbackUser));
        router.push('/assessment');
      }
    } catch (err: any) {
      setIsLoading(false);
      const code = (err.code || '').toLowerCase();
      const message = (err.message || '');
      if (code === 'auth/popup-closed-by-user' || message.includes('popup-closed-by-user')) {
        throw new Error('Sign-in popup was closed. Please try again.');
      }
      if (
        code.includes('api-key') ||
        code.includes('invalid-api-key') ||
        code.includes('configuration-not-found') ||
        message.includes('auth/api-key-not-valid') ||
        message.includes('auth/invalid-api-key')
      ) {
        throw new Error(
          'Google sign-in is not configured: Invalid or missing Firebase API key. Please check your NEXT_PUBLIC_FIREBASE_API_KEY in frontend/.env.local or use Email/Password / Quick Demo Access.'
        );
      }
      throw new Error(err.message || 'Google sign-in failed. Please use email/password instead.');
    } finally {
      setIsLoading(false);
    }
  };

  const demoLogin = async () => {
    setIsLoading(true);
    try {
      const res = await demoLoginUser();
      setToken(res.access_token);
      setUser(res.user);
      if (res.user.has_completed_assessment) {
        router.push('/dashboard');
      } else {
        router.push('/assessment');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    // Try Firebase sign-out if it was used (non-critical)
    try {
      const { auth } = await import('@/lib/firebase');
      const { signOut } = await import('firebase/auth');
      if (auth.currentUser) {
        await signOut(auth);
      }
    } catch {}

    clearAuthToken();
    if (typeof window !== 'undefined') {
      localStorage.removeItem('cached_resume_analysis');
    }
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
      const me = await getMe();
      setUser(me);
      if (typeof window !== 'undefined') {
        localStorage.setItem('auth_user', JSON.stringify(me));
      }
      return me;
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
