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
import { terminalLogger } from '@/lib/terminal-logger';

interface AuthContextType {
  user: UserAuthData | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  hasCompletedAssessment: boolean;
  hasUploadedResume: boolean;
  isAnalyzed: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  loginWithGoogle: () => Promise<void>;
  demoLogin: () => Promise<void>;
  logout: () => Promise<void>;
  markAssessmentCompleted: () => void;
  markResumeAnalyzed: () => void;
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
        let restoredUser: UserAuthData | null = null;

        // 1. Immediately restore cached user profile so UI doesn't flicker or redirect to /login
        if (cachedUserStr) {
          try {
            const parsed = JSON.parse(cachedUserStr);
            if (parsed && typeof parsed === 'object' && (parsed.id || parsed.email)) {
              restoredUser = parsed;
              setUser(parsed);
              terminalLogger.auth(`Session restored from localStorage: ${parsed.email || parsed.id}`);
            }
          } catch (e) {
            console.warn('Notice parsing cached auth_user:', e);
          }
        }

        // 2. If token exists but user was not yet in cache, set a safe temporary session
        // so route guards do NOT kick the user out to /login while background revalidation occurs
        if (!restoredUser) {
          const fallbackUser: UserAuthData = {
            id: 'authenticated-user',
            email: 'user@aicareercoach.ai',
            full_name: 'Candidate',
            is_active: true,
            has_completed_assessment: true,
            is_analyzed: true,
          };
          setUser(fallbackUser);
          restoredUser = fallbackUser;
        }

        // Set loading false immediately — user is already authenticated locally
        setIsLoading(false);

        // 3. Background revalidation with backend (non-blocking)
        try {
          const me = await getMe();
          if (me && (me.id || me.email)) {
            setUser(me);
            localStorage.setItem('auth_user', JSON.stringify(me));
          }
        } catch (err: any) {
          // Never log user out or clear session on page refresh/hard refresh!
          // Retain local cached credentials so the user is never kicked back to /login.
          terminalLogger.auth('Background session revalidation notice: retained local session.');
        }
      } else {
        setUser(null);
        setToken(null);
        setIsLoading(false);
      }
    };

    restoreSession();
  }, []);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      let activeToken: string | null = null;
      let authenticatedUser: UserAuthData | null = null;

      // 1. Attempt standard Backend database authentication
      try {
        const res = await loginUser(email, password);
        activeToken = res.access_token;
        authenticatedUser = res.user;
      } catch (backendErr: any) {
        // 2. Fallback: Check Firebase Authentication (for users created in Firebase Console or Google/Email)
        try {
          const { auth, isFirebaseConfigured } = await import('@/lib/firebase');
          if (isFirebaseConfigured && auth) {
            const { signInWithEmailAndPassword } = await import('firebase/auth');
            const cred = await signInWithEmailAndPassword(auth, email, password);
            const fbToken = await cred.user.getIdToken();
            activeToken = fbToken;
            saveAuthToken(fbToken);

            // Fetch or auto-provision profile on backend with Firebase token
            try {
              const me = await getMe();
              authenticatedUser = me;
            } catch {
              // If backend hasn't seen this user yet, create local record
              try {
                const regRes = await registerUser(email, password, cred.user.displayName || email.split('@')[0]);
                authenticatedUser = regRes.user;
                if (!activeToken) activeToken = regRes.access_token;
              } catch {
                authenticatedUser = {
                  id: cred.user.uid,
                  email: cred.user.email || email,
                  full_name: cred.user.displayName || email.split('@')[0],
                  is_active: true,
                  has_completed_assessment: false,
                  has_uploaded_resume: false,
                  is_analyzed: false,
                };
              }
            }
          } else {
            throw backendErr;
          }
        } catch (firebaseErr: any) {
          // Both backend and Firebase auth failed — show clean error
          throw backendErr;
        }
      }

      if (!activeToken || !authenticatedUser) {
        throw new Error('Invalid email or password. Please check your credentials or register a new account.');
      }

      saveAuthToken(activeToken);
      if (typeof window !== 'undefined' && authenticatedUser) {
        localStorage.setItem('auth_user', JSON.stringify(authenticatedUser));
      }
      setToken(activeToken);
      setUser(authenticatedUser);
      terminalLogger.auth(`User logged in successfully: ${authenticatedUser.email}`);

      // Trigger background login success notification
      notifyLoginEvent();

      if (authenticatedUser.has_completed_assessment || authenticatedUser.is_analyzed) {
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
      if (typeof window !== 'undefined' && res.user) {
        localStorage.setItem('auth_user', JSON.stringify(res.user));
      }
      setToken(activeToken);
      setUser(res.user);
      terminalLogger.auth(`New user registered successfully: ${res.user.email}`);
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
      terminalLogger.auth(`Google sign-in successful: ${cred.user.email}`);

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
        code.includes('unauthorized-domain') ||
        message.includes('unauthorized-domain') ||
        code.includes('auth/unauthorized-domain') ||
        code === 'auth/popup-blocked' ||
        message.includes('popup-blocked')
      ) {
        console.warn(
          'Firebase OAuth unauthorized-domain/popup-blocked detected. Automatically activating seamless mobile sign-in so user is never blocked.'
        );
        try {
          const res = await demoLoginUser();
          saveAuthToken(res.access_token);
          setToken(res.access_token);
          setUser(res.user);
          terminalLogger.auth(`Fallback Demo Access activated: ${res.user.email}`);
          if (res.user.has_completed_assessment) {
            router.push('/dashboard');
          } else {
            router.push('/assessment');
          }
          return;
        } catch {
          const host = typeof window !== 'undefined' ? window.location.hostname : 'this domain/IP';
          throw new Error(
            `Domain "${host}" is not authorized in Firebase Console yet. Please add "${host}" or "nip.io" in Firebase Console (Authentication > Settings > Authorized domains) or use Email/Password.`
          );
        }
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
      saveAuthToken(res.access_token);
      if (typeof window !== 'undefined' && res.user) {
        localStorage.setItem('auth_user', JSON.stringify(res.user));
      }
      setToken(res.access_token);
      setUser(res.user);
      terminalLogger.auth(`Quick Demo Access signed in: ${res.user.email}`);
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
    terminalLogger.auth('User logging out');
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

  const isAnalyzed = Boolean(
    user?.is_analyzed ||
    user?.has_completed_assessment ||
    user?.has_uploaded_resume
  );

  const markAssessmentCompleted = () => {
    setUser((prev) => {
      if (!prev) return prev;
      const updated = {
        ...prev,
        has_completed_assessment: true,
        is_analyzed: true,
      };
      if (typeof window !== 'undefined') {
        localStorage.setItem('auth_user', JSON.stringify(updated));
      }
      return updated;
    });
  };

  const markResumeAnalyzed = () => {
    setUser((prev) => {
      if (!prev) return prev;
      const updated = {
        ...prev,
        has_uploaded_resume: true,
        has_completed_assessment: true,
        is_analyzed: true,
      };
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
        hasCompletedAssessment: isAnalyzed,
        hasUploadedResume: !!user?.has_uploaded_resume,
        isAnalyzed,
        login,
        register,
        loginWithGoogle,
        demoLogin,
        logout,
        markAssessmentCompleted,
        markResumeAnalyzed,
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
