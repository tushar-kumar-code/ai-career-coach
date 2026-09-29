'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import {
  GraduationCap,
  Eye,
  EyeOff,
  Loader2,
  AlertCircle,
  Zap,
  ArrowLeft,
  KeyRound,
  Fingerprint,
  CheckCircle2,
  Brain,
} from 'lucide-react';
import {
  sendOtp,
  verifyOtpLogin,
  verifyOtpReset,
} from '@/lib/api-client';

type AuthMode = 'login' | 'otp-login' | 'forgot-password' | 'another-ways';

export default function LoginPage() {
  const [mode, setMode] = useState<AuthMode>('login');

  // Standard Login State
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDemoSubmitting, setIsDemoSubmitting] = useState(false);
  const [isGoogleSubmitting, setIsGoogleSubmitting] = useState(false);

  // OTP / 2FA Login State
  const [otpEmail, setOtpEmail] = useState('');
  const [otpCode, setOtpCode] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [otpNotice, setOtpNotice] = useState<string | null>(null);
  const [isSendingOtp, setIsSendingOtp] = useState(false);
  const [isVerifyingOtp, setIsVerifyingOtp] = useState(false);

  // Forgot Password / Reset State
  const [resetEmail, setResetEmail] = useState('');
  const [resetOtp, setResetOtp] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [resetStep, setResetStep] = useState<'request' | 'verify'>('request');
  const [resetStatus, setResetStatus] = useState<{ success: boolean; message: string } | null>(null);
  const [isResetting, setIsResetting] = useState(false);

  const { login, demoLogin, loginWithGoogle, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, isLoading, router]);

  // Handle Google OAuth Sign-In
  const handleGoogleLogin = async () => {
    setError(null);
    setIsGoogleSubmitting(true);
    try {
      await loginWithGoogle();
    } catch (err: any) {
      setError(err.message || 'Google sign-in failed. Please try again or use email.');
    } finally {
      setIsGoogleSubmitting(false);
    }
  };

  // Handle Standard Email/Password Login
  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password) {
      setError('Please enter both email and password.');
      return;
    }

    setError(null);
    setIsSubmitting(true);

    try {
      await login(email.trim(), password);
    } catch (err: any) {
      setError(err.message || 'Login failed. Please verify your credentials.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // 1-Click Instant Demo Login
  const handleDemoLogin = async () => {
    setError(null);
    setIsDemoSubmitting(true);
    try {
      await demoLogin();
    } catch (err: any) {
      setError(err.message || 'Demo login failed. Please try standard login.');
    } finally {
      setIsDemoSubmitting(false);
    }
  };

  // Send OTP for 2FA Login
  const handleSendOtpLogin = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!otpEmail.trim()) {
      setError('Please enter your email address to receive verification code.');
      return;
    }

    setError(null);
    setIsSendingOtp(true);

    try {
      const res = await sendOtp(otpEmail.trim(), 'login');
      setOtpSent(true);
      setOtpNotice(res.message);
    } catch (err: any) {
      setError(err.message || 'Failed to send verification code.');
    } finally {
      setIsSendingOtp(false);
    }
  };

  // Verify OTP and Login
  const handleVerifyOtpLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!otpCode.trim() || otpCode.trim().length !== 6) {
      setError('Please enter the 6-digit verification code.');
      return;
    }

    setError(null);
    setIsVerifyingOtp(true);

    try {
      await verifyOtpLogin(otpEmail.trim(), otpCode.trim());
      window.location.href = '/dashboard';
    } catch (err: any) {
      setError(err.message || 'Verification failed. Please check your code.');
    } finally {
      setIsVerifyingOtp(false);
    }
  };

  // Send Real Password Reset Email with Smart Delivery
  const handleForgotPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resetEmail.trim()) {
      setResetStatus({ success: false, message: 'Please enter your registered email address.' });
      return;
    }
    setIsResetting(true);
    setResetStatus(null);

    // 1. Try Firebase / Google official email delivery (works instantly without local SMTP setup)
    try {
      const { auth } = await import('@/lib/firebase');
      const { sendPasswordResetEmail } = await import('firebase/auth');
      await sendPasswordResetEmail(auth, resetEmail.trim());
      setResetStatus({
        success: true,
        message: `Official Password Reset email dispatched to ${resetEmail.trim()}! Please check your mobile inbox or spam folder.`
      });
      return;
    } catch (fbErr: any) {
      // 2. If Firebase fails, try backend OTP delivery
      try {
        const res = await sendOtp(resetEmail.trim(), 'reset');
        setResetStep('verify');
        setResetOtp('');
        setResetStatus({ success: true, message: res.message || 'Real verification code sent to your email.' });
      } catch (backendErr: any) {
        const fbCode = fbErr.code || '';
        if (fbCode === 'auth/user-not-found') {
          setResetStatus({
            success: false,
            message: 'No account found with this email. Please check your spelling or sign up.'
          });
        } else {
          setResetStatus({
            success: false,
            message: fbErr.message || backendErr.message || 'Unable to send password reset email.'
          });
        }
      }
    } finally {
      setIsResetting(false);
    }
  };

  // Confirm Reset with OTP + New Password
  const handleConfirmReset = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resetOtp || resetOtp.length !== 6) {
      setResetStatus({ success: false, message: 'Please enter the 6-digit verification code.' });
      return;
    }
    if (!newPassword || newPassword.length < 6) {
      setResetStatus({ success: false, message: 'New password must be at least 6 characters.' });
      return;
    }
    if (newPassword !== confirmPassword) {
      setResetStatus({ success: false, message: 'Passwords do not match.' });
      return;
    }

    setIsResetting(true);
    setResetStatus(null);

    try {
      const res = await verifyOtpReset(resetEmail.trim(), resetOtp.trim(), newPassword);
      setResetStatus({ success: true, message: res.message || 'Password reset successfully!' });
      setEmail(resetEmail.trim());
      setPassword(newPassword);
      setTimeout(() => {
        setMode('login');
        setResetStatus(null);
        setResetStep('request');
      }, 1500);
    } catch (err: any) {
      setResetStatus({ success: false, message: err.message || 'Failed to verify code and reset password.' });
    } finally {
      setIsResetting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC] dark:bg-[#0F172A] text-[#0F172A] dark:text-[#F1F5F9] flex flex-col justify-between selection:bg-blue-600 selection:text-white">
      {/* Top Header Bar */}
      <header className="w-full px-6 sm:px-10 py-5 flex items-center justify-between border-b border-[#E2E8F0] dark:border-[#334155] bg-transparent">
        <Link href="/" className="flex items-center space-x-2.5 group">
          <div className="w-9 h-9 rounded-xl bg-[#17324D] dark:bg-[#102A43] flex items-center justify-center text-white shadow-sm group-hover:scale-105 transition">
            <Brain className="w-5 h-5 text-[#2563EB]" />
          </div>
          <span className="font-bold text-lg text-[#17324D] dark:text-[#F1F5F9] tracking-tight">Career</span>
        </Link>
        <span className="text-xs sm:text-sm font-medium text-[#64748B] dark:text-[#A8B3C2]">
          Your Career, Your Future
        </span>
      </header>

      {/* Center Auth Card */}
      <div className="flex-1 flex items-center justify-center p-4 sm:p-6 my-4">
        <div className="w-full max-w-[420px] bg-white dark:bg-[#172235] rounded-3xl border border-[#E2E8F0] dark:border-[#334155] p-7 sm:p-9 shadow-sm">
          
          {/* Top Floating Badge */}
          <div className="flex justify-center mb-5">
            <div className="w-14 h-14 rounded-2xl bg-[#F8FAFC] dark:bg-[#102A43] border border-[#E2E8F0] dark:border-[#334155] flex items-center justify-center shadow-xs">
              <GraduationCap className="w-7 h-7 text-[#17324D] dark:text-[#38BDF8]" />
            </div>
          </div>

          {/* ════════════ 1. STANDARD LOGIN MODE ════════════ */}
          {mode === 'login' && (
            <>
              {/* Title & Subtitle */}
              <div className="text-center mb-7">
                <h1 className="text-2xl sm:text-3xl font-extrabold text-[#17324D] dark:text-[#F1F5F9] tracking-tight">
                  Welcome back
                </h1>
                <p className="text-xs sm:text-sm text-[#64748B] dark:text-[#A8B3C2] mt-1.5">
                  Continue your journey towards your dream career.
                </p>
              </div>

              {/* Error Banner */}
              {error && (
                <div className="mb-5 p-3.5 rounded-xl bg-rose-500/10 border border-[#C75C5C]/30 text-[#C75C5C] text-xs flex items-start gap-2.5 animate-in fade-in">
                  <AlertCircle className="w-4 h-4 text-[#C75C5C] shrink-0 mt-0.5" />
                  <span>{error}</span>
                </div>
              )}

              {/* Login Form */}
              <form onSubmit={handleLoginSubmit} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-[#0F172A] dark:text-[#F1F5F9] mb-1.5">
                    Email address
                  </label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@example.com"
                    required
                    className="w-full bg-white dark:bg-[#102A43] border border-[#E2E8F0] dark:border-[#334155] rounded-xl px-4 py-3 text-sm text-[#0F172A] dark:text-[#F1F5F9] placeholder-[#94A3B8] focus:outline-none focus:border-[#17324D] dark:focus:border-[#2563EB] transition"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-[#0F172A] dark:text-[#F1F5F9] mb-1.5">
                    Password
                  </label>
                  <div className="relative">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Enter your password"
                      required
                      className="w-full bg-white dark:bg-[#102A43] border border-[#E2E8F0] dark:border-[#334155] rounded-xl pl-4 pr-11 py-3 text-sm text-[#0F172A] dark:text-[#F1F5F9] placeholder-[#94A3B8] focus:outline-none focus:border-[#17324D] dark:focus:border-[#2563EB] transition"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3.5 top-1/2 -translate-y-1/2 text-[#94A3B8] hover:text-[#0F172A] dark:hover:text-[#F1F5F9] p-1"
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  <div className="text-right mt-1.5">
                    <button
                      type="button"
                      onClick={() => {
                        setResetEmail(email);
                        setResetStatus(null);
                        setResetStep('request');
                        setMode('forgot-password');
                      }}
                      className="text-xs font-medium text-[#17324D] dark:text-[#38BDF8] hover:underline"
                    >
                      Forgot password?
                    </button>
                  </div>
                </div>

                {/* Primary Log In Button */}
                <button
                  type="submit"
                  disabled={isSubmitting || isDemoSubmitting || isGoogleSubmitting}
                  className="w-full py-3.5 px-4 rounded-xl font-bold text-sm bg-[#17324D] hover:bg-[#102A43] text-white transition shadow-sm flex items-center justify-center space-x-2 disabled:opacity-50 mt-2 cursor-pointer"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin text-[#2563EB]" />
                      <span>Logging in...</span>
                    </>
                  ) : (
                    <span>Log in</span>
                  )}
                </button>
              </form>

              {/* OR Divider */}
              <div className="flex items-center space-x-3 my-5 text-[#94A3B8] dark:text-[#64748B] text-xs font-medium uppercase">
                <div className="flex-1 h-px bg-[#E2E8F0] dark:bg-[#334155]" />
                <span className="px-1 text-[11px] tracking-wider">OR</span>
                <div className="flex-1 h-px bg-[#E2E8F0] dark:bg-[#334155]" />
              </div>

              {/* Continue with Google */}
              <button
                type="button"
                onClick={handleGoogleLogin}
                disabled={isGoogleSubmitting || isSubmitting || isDemoSubmitting}
                className="w-full py-3 px-4 rounded-xl font-medium text-xs sm:text-sm bg-white dark:bg-[#102A43] hover:bg-[#F8FAFC] dark:hover:bg-[#172235] border border-[#E2E8F0] dark:border-[#334155] text-[#0F172A] dark:text-[#F1F5F9] transition flex items-center justify-center space-x-2.5 shadow-xs disabled:opacity-50 cursor-pointer"
              >
                {isGoogleSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin text-[#2563EB]" />
                    <span>Connecting with Google...</span>
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24">
                      <path
                        fill="#4285F4"
                        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                      />
                      <path
                        fill="#34A853"
                        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                      />
                      <path
                        fill="#FBBC05"
                        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                      />
                      <path
                        fill="#EA4335"
                        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                      />
                    </svg>
                    <span>Continue with Google</span>
                  </>
                )}
              </button>

              {/* Quick Demo Access */}
              <div className="mt-3">
                <button
                  type="button"
                  onClick={handleDemoLogin}
                  disabled={isDemoSubmitting || isSubmitting || isGoogleSubmitting}
                  className="w-full py-2.5 px-4 rounded-xl text-xs font-semibold bg-[#F8FAFC] dark:bg-[#1E2D44] hover:bg-[#F1F5F9] dark:hover:bg-[#253752] border border-[#E2E8F0] dark:border-[#334155] text-[#17324D] dark:text-[#38BDF8] transition flex items-center justify-center space-x-2 disabled:opacity-50 cursor-pointer"
                >
                  {isDemoSubmitting ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin text-[#2563EB]" />
                      <span>Opening Demo Cockpit...</span>
                    </>
                  ) : (
                    <>
                      <Zap className="w-3.5 h-3.5 text-[#2563EB]" />
                      <span>Quick Demo Access (Explore Platform)</span>
                    </>
                  )}
                </button>
              </div>

              {/* Try Another Way (OTP 2FA) */}
              <div className="text-center mt-3">
                <button
                  type="button"
                  onClick={() => {
                    setOtpEmail(email);
                    setError(null);
                    setMode('another-ways');
                  }}
                  className="text-xs text-[#64748B] dark:text-[#A8B3C2] hover:text-[#17324D] dark:hover:text-[#F1F5F9] font-medium transition"
                >
                  Try another way to sign in (OTP / 2FA)
                </button>
              </div>

              {/* Footer Switch */}
              <div className="text-center pt-4 mt-4 border-t border-[#E2E8F0] dark:border-[#334155] text-xs text-[#64748B] dark:text-[#A8B3C2]">
                Don&apos;t have an account?{' '}
                <Link
                  href="/register"
                  className="text-[#17324D] dark:text-[#38BDF8] font-bold hover:underline"
                >
                  Sign up
                </Link>
              </div>
            </>
          )}

          {/* ════════════ 2. TRY ANOTHER WAY (OTP / 2FA) ════════════ */}
          {mode === 'another-ways' && (
            <div className="space-y-4 animate-in fade-in">
              <div className="text-center mb-6">
                <h2 className="text-xl font-bold text-[#17324D] dark:text-[#F1F5F9]">
                  Choose How to Sign In
                </h2>
                <p className="text-xs text-[#64748B] dark:text-[#A8B3C2] mt-1">
                  Select your preferred authentication method:
                </p>
              </div>

              <div className="space-y-3">
                <button
                  type="button"
                  onClick={() => {
                    setOtpEmail(email);
                    setMode('otp-login');
                  }}
                  className="w-full p-4 rounded-2xl bg-white dark:bg-[#102A43] border border-[#E2E8F0] dark:border-[#334155] hover:border-[#17324D] dark:hover:border-[#2563EB] text-left transition flex items-center space-x-3.5 group"
                >
                  <div className="w-10 h-10 rounded-xl bg-[#F8FAFC] dark:bg-[#172235] border border-[#E2E8F0] dark:border-[#334155] flex items-center justify-center text-[#17324D] dark:text-[#38BDF8] group-hover:scale-105 transition">
                    <Fingerprint className="w-5 h-5" />
                  </div>
                  <div className="flex-1">
                    <div className="text-xs font-bold text-[#17324D] dark:text-[#F1F5F9]">
                      Sign in with Email Verification Code (OTP)
                    </div>
                    <div className="text-[11px] text-[#64748B] dark:text-[#A8B3C2]">
                      Receive a 6-digit one-time code on your email
                    </div>
                  </div>
                </button>

                <button
                  type="button"
                  onClick={handleDemoLogin}
                  disabled={isDemoSubmitting}
                  className="w-full p-4 rounded-2xl bg-white dark:bg-[#102A43] border border-[#E2E8F0] dark:border-[#334155] hover:border-[#17324D] dark:hover:border-[#2563EB] text-left transition flex items-center space-x-3.5 group"
                >
                  <div className="w-10 h-10 rounded-xl bg-[#F8FAFC] dark:bg-[#172235] border border-[#E2E8F0] dark:border-[#334155] flex items-center justify-center text-[#2563EB] group-hover:scale-105 transition">
                    <Zap className="w-5 h-5" />
                  </div>
                  <div className="flex-1">
                    <div className="text-xs font-bold text-[#17324D] dark:text-[#F1F5F9]">
                      1-Click Instant Demo Login
                    </div>
                    <div className="text-[11px] text-[#64748B] dark:text-[#A8B3C2]">
                      Instant access with preloaded demo profile
                    </div>
                  </div>
                </button>
              </div>

              <div className="pt-3">
                <button
                  type="button"
                  onClick={() => setMode('login')}
                  className="w-full py-2.5 text-xs text-[#64748B] dark:text-[#A8B3C2] hover:text-[#17324D] dark:hover:text-[#F1F5F9] font-semibold transition flex items-center justify-center space-x-1.5"
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                  <span>Back to Standard Login</span>
                </button>
              </div>
            </div>
          )}

          {/* ════════════ 3. OTP 2FA LOGIN MODE ════════════ */}
          {mode === 'otp-login' && (
            <div className="space-y-4 animate-in fade-in">
              <div className="text-center mb-6">
                <h2 className="text-xl font-bold text-[#17324D] dark:text-[#F1F5F9]">
                  2-Factor / OTP Quick Sign In
                </h2>
                <p className="text-xs text-[#64748B] dark:text-[#A8B3C2] mt-1">
                  Sign in securely with a 6-digit verification code.
                </p>
              </div>

              {error && (
                <div className="p-3.5 rounded-xl bg-rose-500/10 border border-[#C75C5C]/30 text-[#C75C5C] text-xs flex items-start gap-2.5">
                  <AlertCircle className="w-4 h-4 text-[#C75C5C] shrink-0 mt-0.5" />
                  <span>{error}</span>
                </div>
              )}

              {!otpSent ? (
                <form onSubmit={handleSendOtpLogin} className="space-y-4">
                  <div>
                    <label className="block text-xs font-semibold text-[#0F172A] dark:text-[#F1F5F9] mb-1.5">
                      Enter Your Email
                    </label>
                    <input
                      type="email"
                      value={otpEmail}
                      onChange={(e) => setOtpEmail(e.target.value)}
                      placeholder="you@example.com"
                      required
                      className="w-full bg-white dark:bg-[#102A43] border border-[#E2E8F0] dark:border-[#334155] rounded-xl px-4 py-3 text-sm text-[#0F172A] dark:text-[#F1F5F9] placeholder-[#94A3B8] focus:outline-none focus:border-[#17324D]"
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={isSendingOtp}
                    className="w-full py-3.5 rounded-xl font-bold text-sm bg-[#17324D] hover:bg-[#102A43] text-white transition flex items-center justify-center space-x-2"
                  >
                    {isSendingOtp ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin text-[#2563EB]" />
                        <span>Sending Code...</span>
                      </>
                    ) : (
                      <span>Send 6-Digit Code</span>
                    )}
                  </button>
                </form>
              ) : (
                <form onSubmit={handleVerifyOtpLogin} className="space-y-4">
                  {otpNotice && (
                    <div className="p-3 rounded-xl bg-[#2E7D5B]/10 border border-[#2E7D5B]/30 text-[#2E7D5B] text-xs flex items-center space-x-2">
                      <CheckCircle2 className="w-4 h-4 shrink-0" />
                      <span>{otpNotice}</span>
                    </div>
                  )}
                  <div>
                    <label className="block text-xs font-semibold text-[#0F172A] dark:text-[#F1F5F9] mb-1.5">
                      Enter 6-Digit Code
                    </label>
                    <input
                      type="text"
                      maxLength={6}
                      value={otpCode}
                      onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ''))}
                      placeholder="123456"
                      required
                      className="w-full text-center tracking-widest text-lg font-mono font-bold bg-white dark:bg-[#102A43] border border-[#E2E8F0] dark:border-[#334155] rounded-xl py-3 text-[#17324D] dark:text-[#F1F5F9] focus:outline-none focus:border-[#17324D]"
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={isVerifyingOtp}
                    className="w-full py-3.5 rounded-xl font-bold text-sm bg-[#17324D] hover:bg-[#102A43] text-white transition flex items-center justify-center space-x-2"
                  >
                    {isVerifyingOtp ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin text-[#2563EB]" />
                        <span>Verifying & Signing In...</span>
                      </>
                    ) : (
                      <span>Verify & Access Platform</span>
                    )}
                  </button>
                </form>
              )}

              <div className="pt-2 text-center">
                <button
                  type="button"
                  onClick={() => setMode('login')}
                  className="text-xs text-[#64748B] hover:text-[#17324D] dark:hover:text-[#F1F5F9] font-medium"
                >
                  ← Back to Email/Password Login
                </button>
              </div>
            </div>
          )}

          {/* ════════════ 4. FORGOT PASSWORD MODE ════════════ */}
          {mode === 'forgot-password' && (
            <div className="space-y-4 animate-in fade-in">
              <div className="text-center mb-6">
                <h2 className="text-xl font-bold text-[#17324D] dark:text-[#F1F5F9]">
                  Reset Your Password
                </h2>
                <p className="text-xs text-[#64748B] dark:text-[#A8B3C2] mt-1">
                  {resetStep === 'request'
                    ? 'Enter your registered email to receive a reset code.'
                    : 'Enter the code and set your new password.'}
                </p>
              </div>

              {resetStatus && (
                <div
                  className={`p-3.5 rounded-xl text-xs flex items-start gap-2.5 ${
                    resetStatus.success
                      ? 'bg-[#2E7D5B]/10 border border-[#2E7D5B]/30 text-[#2E7D5B]'
                      : 'bg-rose-500/10 border border-[#C75C5C]/30 text-[#C75C5C]'
                  }`}
                >
                  {resetStatus.success ? (
                    <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
                  ) : (
                    <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                  )}
                  <span>{resetStatus.message}</span>
                </div>
              )}

              {resetStep === 'request' ? (
                <form onSubmit={handleForgotPassword} className="space-y-4">
                  <div>
                    <label className="block text-xs font-semibold text-[#0F172A] dark:text-[#F1F5F9] mb-1.5">
                      Your Registered Email
                    </label>
                    <input
                      type="email"
                      value={resetEmail}
                      onChange={(e) => setResetEmail(e.target.value)}
                      placeholder="you@example.com"
                      required
                      className="w-full bg-white dark:bg-[#102A43] border border-[#E2E8F0] dark:border-[#334155] rounded-xl px-4 py-3 text-sm text-[#0F172A] dark:text-[#F1F5F9] placeholder-[#94A3B8] focus:outline-none focus:border-[#17324D]"
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={isResetting}
                    className="w-full py-3.5 rounded-xl font-bold text-sm bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white shadow-lg transition flex items-center justify-center space-x-2"
                  >
                    {isResetting ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin text-white" />
                        <span>Sending Reset Email...</span>
                      </>
                    ) : (
                      <span>📧 Send Password Reset Email</span>
                    )}
                  </button>

                  <div className="pt-1 text-center">
                    <button
                      type="button"
                      onClick={() => setResetStep('verify')}
                      className="text-xs text-[#2563EB] hover:underline font-medium"
                    >
                      Already have a 6-digit verification code? Click here
                    </button>
                  </div>
                </form>
              ) : (
                <form onSubmit={handleConfirmReset} className="space-y-4">
                  <div>
                    <label className="block text-xs font-semibold text-[#0F172A] dark:text-[#F1F5F9] mb-1.5">
                      6-Digit Reset Code
                    </label>
                    <input
                      type="text"
                      maxLength={6}
                      value={resetOtp}
                      onChange={(e) => setResetOtp(e.target.value.replace(/\D/g, ''))}
                      placeholder="123456"
                      required
                      className="w-full text-center tracking-widest text-lg font-mono font-bold bg-white dark:bg-[#102A43] border border-[#E2E8F0] dark:border-[#334155] rounded-xl py-3 text-[#17324D] dark:text-[#F1F5F9] focus:outline-none focus:border-[#17324D]"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-[#0F172A] dark:text-[#F1F5F9] mb-1.5">
                      New Password
                    </label>
                    <input
                      type="password"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      placeholder="Min. 6 characters"
                      required
                      className="w-full bg-white dark:bg-[#102A43] border border-[#E2E8F0] dark:border-[#334155] rounded-xl px-4 py-3 text-sm text-[#0F172A] dark:text-[#F1F5F9] focus:outline-none focus:border-[#17324D]"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-[#0F172A] dark:text-[#F1F5F9] mb-1.5">
                      Confirm New Password
                    </label>
                    <input
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="Re-enter password"
                      required
                      className="w-full bg-white dark:bg-[#102A43] border border-[#E2E8F0] dark:border-[#334155] rounded-xl px-4 py-3 text-sm text-[#0F172A] dark:text-[#F1F5F9] focus:outline-none focus:border-[#17324D]"
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={isResetting}
                    className="w-full py-3.5 rounded-xl font-bold text-sm bg-[#17324D] hover:bg-[#102A43] text-white transition flex items-center justify-center space-x-2"
                  >
                    {isResetting ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin text-[#2563EB]" />
                        <span>Updating Password...</span>
                      </>
                    ) : (
                      <span>Reset Password & Sign In</span>
                    )}
                  </button>
                </form>
              )}

              <div className="pt-2 text-center">
                <button
                  type="button"
                  onClick={() => setMode('login')}
                  className="text-xs text-[#64748B] hover:text-[#17324D] dark:hover:text-[#F1F5F9] font-medium"
                >
                  ← Back to Login
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Bottom Page Footer */}
      <footer className="w-full text-center py-5 text-xs text-[#64748B] dark:text-[#A8B3C2]">
        By continuing, you agree to our{' '}
        <Link href="/" className="hover:underline text-[#0F172A] dark:text-[#F1F5F9]">Terms of Service</Link> and{' '}
        <Link href="/" className="hover:underline text-[#0F172A] dark:text-[#F1F5F9]">Privacy Policy</Link>.
      </footer>
    </div>
  );
}
