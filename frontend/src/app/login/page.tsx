'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import {
  Sparkles,
  Lock,
  Mail,
  Eye,
  EyeOff,
  ArrowRight,
  Loader2,
  AlertCircle,
  Zap,
  ShieldCheck,
  CheckCircle2,
  KeyRound,
  ArrowLeft,
  Smartphone,
  Fingerprint,
  RefreshCw,
} from 'lucide-react';
import {
  resetPassword,
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
  const [devCodeBanner, setDevCodeBanner] = useState<string | null>(null);

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
    setDevCodeBanner(null);

    try {
      const res = await sendOtp(otpEmail.trim(), 'login');
      setOtpSent(true);
      setOtpNotice(res.message);
      if (res.dev_code) {
        setDevCodeBanner(res.dev_code);
        setOtpCode(res.dev_code); // auto-fill for instant convenience
      }
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
      // Refresh window state to trigger AuthContext detection & redirect
      window.location.href = '/dashboard';
    } catch (err: any) {
      setError(err.message || 'Verification failed. Please check your code.');
    } finally {
      setIsVerifyingOtp(false);
    }
  };

  // Send OTP for Password Reset
  const handleSendResetOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resetEmail.trim()) {
      setResetStatus({ success: false, message: 'Please enter your registered email.' });
      return;
    }

    setIsResetting(true);
    setResetStatus(null);

    try {
      const res = await sendOtp(resetEmail.trim(), 'reset');
      setResetStep('verify');
      if (res.dev_code) {
        setResetOtp(res.dev_code);
        setDevCodeBanner(res.dev_code);
      }
      setResetStatus({ success: true, message: 'Verification code sent to your email.' });
    } catch (err: any) {
      setResetStatus({ success: false, message: err.message || 'Email not found.' });
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
    <div className="min-h-screen bg-[#FAF8F3] dark:bg-[#0F172A] text-[#273444] dark:text-[#F1F5F9] flex flex-col justify-center items-center p-4 sm:p-6 relative selection:bg-[#B89B72] selection:text-white">
      {/* Main Container */}
      <div className="relative w-full max-w-md">
        {/* Brand Header */}
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center space-x-3 group mb-4">
            <div className="w-12 h-12 rounded-2xl bg-[#17324D] dark:bg-[#102A43] border border-[#B89B72]/40 flex items-center justify-center shadow-sm group-hover:scale-105 transition">
              <Sparkles className="w-6 h-6 text-[#B89B72]" />
            </div>
            <span className="font-extrabold text-2xl text-[#17324D] dark:text-[#F1F5F9] tracking-tight">AI Career Coach</span>
          </Link>

          <h1 className="text-xl sm:text-2xl font-bold text-[#17324D] dark:text-[#F1F5F9] tracking-tight">
            {mode === 'login' && 'Sign in to Career Cockpit'}
            {mode === 'otp-login' && '2-Factor / OTP Quick Sign In'}
            {mode === 'another-ways' && 'Choose How to Sign In'}
            {mode === 'forgot-password' && 'Reset Your Password'}
          </h1>
          <p className="text-xs sm:text-sm text-[#64748B] dark:text-[#A8B3C2] mt-1">
            {mode === 'login' && 'Access your digital twin, roadmap & mock interviews'}
            {mode === 'otp-login' && 'Sign in instantly with a 6-digit verification code'}
            {mode === 'another-ways' && 'Select your preferred verification method'}
            {mode === 'forgot-password' && 'Verify your identity and set a new password'}
          </p>
        </div>

        {/* Card */}
        <div className="p-6 sm:p-8 rounded-3xl bg-white dark:bg-[#172235] border border-[#E7E2D8] dark:border-[#334155] shadow-sm space-y-6">

          {/* ════════════ 1. STANDARD LOGIN ════════════ */}
          {mode === 'login' && (
            <>
              {/* Google Sign In Button */}
              <button
                type="button"
                onClick={handleGoogleLogin}
                disabled={isGoogleSubmitting || isSubmitting || isDemoSubmitting}
                className="w-full py-2.5 px-4 rounded-xl font-semibold text-xs bg-white dark:bg-[#102A43] hover:bg-[#FAF8F3] dark:hover:bg-[#172235] border border-[#E7E2D8] dark:border-[#334155] text-[#273444] dark:text-[#F1F5F9] transition flex items-center justify-center space-x-2.5 shadow-sm disabled:opacity-50"
              >
                {isGoogleSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin text-[#B89B72]" />
                    <span>Signing in with Google...</span>
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

              {/* 1-Click Demo Login */}
              <div className="p-3.5 rounded-2xl bg-[#FAF8F3] dark:bg-[#102A43] border border-[#E7E2D8] dark:border-[#334155] text-center">
                <p className="text-xs text-[#64748B] dark:text-[#A8B3C2] mb-2 font-medium">Want a fast preview without typing?</p>
                <button
                  type="button"
                  onClick={handleDemoLogin}
                  disabled={isDemoSubmitting || isSubmitting || isGoogleSubmitting}
                  className="w-full py-2.5 px-4 rounded-xl font-bold text-xs bg-[#17324D] hover:bg-[#102A43] text-white transition shadow-sm flex items-center justify-center space-x-2 disabled:opacity-50"
                >
                  {isDemoSubmitting ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin text-[#B89B72]" />
                      <span>Logging in to Demo Account...</span>
                    </>
                  ) : (
                    <>
                      <Zap className="w-4 h-4 text-[#B89B72]" />
                      <span>1-Click Instant Demo Login</span>
                    </>
                  )}
                </button>
              </div>

              <div className="flex items-center space-x-3 text-[#64748B] dark:text-[#A8B3C2] text-xs uppercase font-semibold">
                <div className="flex-1 h-px bg-[#E7E2D8] dark:bg-[#334155]" />
                <span>Or Sign in with Email</span>
                <div className="flex-1 h-px bg-[#E7E2D8] dark:bg-[#334155]" />
              </div>

              {/* Error Alert */}
              {error && (
                <div className="p-3.5 rounded-xl bg-rose-500/10 border border-[#C75C5C]/30 text-[#C75C5C] text-xs flex items-start gap-2.5 animate-in fade-in">
                  <AlertCircle className="w-4 h-4 text-[#C75C5C] shrink-0 mt-0.5" />
                  <span>{error}</span>
                </div>
              )}

              {/* Login Form */}
              <form onSubmit={handleLoginSubmit} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-[#273444] dark:text-[#F1F5F9] mb-1.5">
                    Email Address
                  </label>
                  <div className="relative">
                    <Mail className="w-4 h-4 text-[#64748B] dark:text-[#A8B3C2] absolute left-3.5 top-1/2 -translate-y-1/2" />
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="student@university.edu"
                      required
                      className="w-full bg-[#FAF8F3] dark:bg-[#102A43] border border-[#E7E2D8] dark:border-[#334155] rounded-xl pl-10 pr-4 py-2.5 text-sm text-[#273444] dark:text-[#F1F5F9] placeholder-[#64748B] focus:outline-none focus:ring-2 focus:ring-[#B89B72] transition"
                    />
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="text-xs font-semibold text-[#273444] dark:text-[#F1F5F9]">
                      Password
                    </label>
                    <button
                      type="button"
                      onClick={() => {
                        setResetEmail(email);
                        setResetStatus(null);
                        setResetStep('request');
                        setMode('forgot-password');
                      }}
                      className="text-xs text-[#B89B72] hover:text-[#A3845B] hover:underline transition font-semibold"
                    >
                      Forgot password?
                    </button>
                  </div>
                  <div className="relative">
                    <Lock className="w-4 h-4 text-[#64748B] dark:text-[#A8B3C2] absolute left-3.5 top-1/2 -translate-y-1/2" />
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••"
                      required
                      className="w-full bg-[#FAF8F3] dark:bg-[#102A43] border border-[#E7E2D8] dark:border-[#334155] rounded-xl pl-10 pr-10 py-2.5 text-sm text-[#273444] dark:text-[#F1F5F9] placeholder-[#64748B] focus:outline-none focus:ring-2 focus:ring-[#B89B72] transition"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3.5 top-1/2 -translate-y-1/2 text-[#64748B] hover:text-[#273444] dark:hover:text-[#F1F5F9]"
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={isSubmitting || isDemoSubmitting}
                  className="w-full py-3 px-4 rounded-xl font-bold text-sm bg-[#17324D] hover:bg-[#102A43] text-white transition shadow-sm flex items-center justify-center space-x-2 disabled:opacity-50 mt-2"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin text-[#B89B72]" />
                      <span>Signing In...</span>
                    </>
                  ) : (
                    <>
                      <span>Sign In</span>
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </form>

              {/* Try Another Way Button */}
              <div className="pt-2 text-center">
                <button
                  type="button"
                  onClick={() => {
                    setOtpEmail(email);
                    setError(null);
                    setMode('another-ways');
                  }}
                  className="inline-flex items-center space-x-1.5 text-xs text-[#17324D] dark:text-[#D9C19A] hover:text-[#102A43] font-semibold transition hover:underline"
                >
                  <Fingerprint className="w-3.5 h-3.5 text-[#B89B72]" />
                  <span>Try another way to sign in (OTP / 2FA)</span>
                </button>
              </div>

              {/* Footer */}
              <div className="text-center pt-2 border-t border-[#E7E2D8] dark:border-[#334155] text-xs text-[#64748B] dark:text-[#A8B3C2]">
                Don&apos;t have an account yet?{' '}
                <Link
                  href="/register"
                  className="text-[#17324D] dark:text-[#D9C19A] font-semibold hover:underline"
                >
                  Create Account
                </Link>
              </div>
            </>
          )}

          {/* ════════════ 2. TRY ANOTHER WAY OPTIONS ════════════ */}
          {mode === 'another-ways' && (
            <div className="space-y-4 animate-in fade-in">
              <p className="text-xs text-[#64748B] dark:text-[#A8B3C2]">
                Choose an alternative authentication method:
              </p>

              <div className="space-y-3">
                {/* Option A: 2FA OTP Code */}
                <button
                  type="button"
                  onClick={() => {
                    setOtpEmail(email);
                    setOtpSent(false);
                    setError(null);
                    setMode('otp-login');
                  }}
                  className="w-full p-3.5 rounded-2xl bg-white dark:bg-[#102A43] border border-[#E7E2D8] dark:border-[#334155] hover:border-[#B89B72]/60 hover:bg-[#FAF8F3] dark:hover:bg-[#172235] transition flex items-center space-x-3.5 text-left group shadow-sm"
                >
                  <div className="w-10 h-10 rounded-xl bg-[#B89B72]/15 border border-[#B89B72]/30 flex items-center justify-center text-[#B89B72] shrink-0 group-hover:scale-105 transition">
                    <Smartphone className="w-5 h-5" />
                  </div>
                  <div className="flex-1">
                    <p className="text-xs font-bold text-[#17324D] dark:text-[#F1F5F9]">6-Digit OTP / Verification Code</p>
                    <p className="text-[11px] text-[#64748B] dark:text-[#A8B3C2]">No password needed — instant one-time login code</p>
                  </div>
                  <ArrowRight className="w-4 h-4 text-[#64748B] group-hover:text-[#B89B72] transition" />
                </button>

                {/* Option B: 1-Click Instant Demo */}
                <button
                  type="button"
                  onClick={handleDemoLogin}
                  disabled={isDemoSubmitting}
                  className="w-full p-3.5 rounded-2xl bg-white dark:bg-[#102A43] border border-[#E7E2D8] dark:border-[#334155] hover:border-[#B89B72]/60 hover:bg-[#FAF8F3] dark:hover:bg-[#172235] transition flex items-center space-x-3.5 text-left group shadow-sm"
                >
                  <div className="w-10 h-10 rounded-xl bg-[#B89B72]/15 border border-[#B89B72]/30 flex items-center justify-center text-[#B89B72] shrink-0 group-hover:scale-105 transition">
                    <Zap className="w-5 h-5" />
                  </div>
                  <div className="flex-1">
                    <p className="text-xs font-bold text-[#17324D] dark:text-[#F1F5F9]">1-Click Instant Candidate Demo</p>
                    <p className="text-[11px] text-[#64748B] dark:text-[#A8B3C2]">Instantly explore with pre-configured mock profile</p>
                  </div>
                  <ArrowRight className="w-4 h-4 text-[#64748B] group-hover:text-[#B89B72] transition" />
                </button>

                {/* Option C: Reset Password */}
                <button
                  type="button"
                  onClick={() => {
                    setResetEmail(email);
                    setResetStep('request');
                    setResetStatus(null);
                    setMode('forgot-password');
                  }}
                  className="w-full p-3.5 rounded-2xl bg-white dark:bg-[#102A43] border border-[#E7E2D8] dark:border-[#334155] hover:border-[#B89B72]/60 hover:bg-[#FAF8F3] dark:hover:bg-[#172235] transition flex items-center space-x-3.5 text-left group shadow-sm"
                >
                  <div className="w-10 h-10 rounded-xl bg-[#FAF8F3] dark:bg-[#172235] border border-[#E7E2D8] dark:border-[#334155] flex items-center justify-center text-[#17324D] dark:text-[#D9C19A] shrink-0 group-hover:scale-105 transition">
                    <KeyRound className="w-5 h-5" />
                  </div>
                  <div className="flex-1">
                    <p className="text-xs font-bold text-[#17324D] dark:text-[#F1F5F9]">Reset Forgotten Password</p>
                    <p className="text-[11px] text-[#64748B] dark:text-[#A8B3C2]">Set a new password using email verification</p>
                  </div>
                  <ArrowRight className="w-4 h-4 text-[#64748B] group-hover:text-[#17324D] transition" />
                </button>
              </div>

              <div className="pt-2 border-t border-[#E7E2D8] dark:border-[#334155] text-center">
                <button
                  type="button"
                  onClick={() => setMode('login')}
                  className="inline-flex items-center space-x-1.5 text-xs text-[#64748B] dark:text-[#A8B3C2] hover:text-[#17324D] dark:hover:text-white transition"
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                  <span>Back to Standard Sign In</span>
                </button>
              </div>
            </div>
          )}

          {/* ════════════ 3. 2FA / OTP LOGIN ════════════ */}
          {mode === 'otp-login' && (
            <div className="space-y-4 animate-in fade-in">
              <div className="flex items-center space-x-2 text-[#17324D] dark:text-[#D9C19A] bg-[#FAF8F3] dark:bg-[#102A43] border border-[#E7E2D8] dark:border-[#334155] p-3 rounded-xl">
                <Smartphone className="w-4 h-4 shrink-0 text-[#B89B72]" />
                <p className="text-xs text-[#64748B] dark:text-[#A8B3C2]">
                  Enter your email address to receive a 6-digit security code for instant login.
                </p>
              </div>

              {/* Dev Code Quick Auto-Fill Banner */}
              {devCodeBanner && (
                <div className="p-3 rounded-xl bg-emerald-500/10 border border-[#2E7D5B]/30 text-[#2E7D5B] text-xs flex items-center justify-between">
                  <span>Verification Code: <strong className="font-mono text-sm tracking-widest text-[#17324D] dark:text-white ml-1">{devCodeBanner}</strong></span>
                  <span className="text-[10px] bg-[#2E7D5B]/20 px-2 py-0.5 rounded text-[#2E7D5B] font-semibold">Active</span>
                </div>
              )}

              {error && (
                <div className="p-3.5 rounded-xl bg-rose-500/10 border border-[#C75C5C]/30 text-[#C75C5C] text-xs flex items-start gap-2.5 animate-in fade-in">
                  <AlertCircle className="w-4 h-4 text-[#C75C5C] shrink-0 mt-0.5" />
                  <span>{error}</span>
                </div>
              )}

              {!otpSent ? (
                <form onSubmit={handleSendOtpLogin} className="space-y-4">
                  <div>
                    <label className="block text-xs font-semibold text-[#273444] dark:text-[#F1F5F9] mb-1.5">
                      Your Email Address
                    </label>
                    <div className="relative">
                      <Mail className="w-4 h-4 text-[#64748B] dark:text-[#A8B3C2] absolute left-3.5 top-1/2 -translate-y-1/2" />
                      <input
                        type="email"
                        value={otpEmail}
                        onChange={(e) => setOtpEmail(e.target.value)}
                        placeholder="student@university.edu"
                        required
                        className="w-full bg-[#FAF8F3] dark:bg-[#102A43] border border-[#E7E2D8] dark:border-[#334155] rounded-xl pl-10 pr-4 py-2.5 text-sm text-[#273444] dark:text-[#F1F5F9] placeholder-[#64748B] focus:outline-none focus:ring-2 focus:ring-[#B89B72] transition"
                      />
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={isSendingOtp}
                    className="w-full py-3 px-4 rounded-xl font-bold text-sm bg-[#17324D] hover:bg-[#102A43] text-white transition shadow-sm flex items-center justify-center space-x-2 disabled:opacity-50"
                  >
                    {isSendingOtp ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin text-[#B89B72]" />
                        <span>Sending Security Code...</span>
                      </>
                    ) : (
                      <>
                        <Smartphone className="w-4 h-4" />
                        <span>Send 6-Digit Code</span>
                      </>
                    )}
                  </button>
                </form>
              ) : (
                <form onSubmit={handleVerifyOtpLogin} className="space-y-4">
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <label className="text-xs font-semibold text-[#273444] dark:text-[#F1F5F9]">
                        Enter 6-Digit Code for <span className="text-[#B89B72]">{otpEmail}</span>
                      </label>
                      <button
                        type="button"
                        onClick={() => handleSendOtpLogin()}
                        disabled={isSendingOtp}
                        className="text-[11px] text-[#B89B72] hover:underline flex items-center gap-1 font-semibold"
                      >
                        <RefreshCw className="w-3 h-3" /> Resend
                      </button>
                    </div>
                    <input
                      type="text"
                      maxLength={6}
                      value={otpCode}
                      onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ''))}
                      placeholder="123456"
                      required
                      autoFocus
                      className="w-full bg-[#FAF8F3] dark:bg-[#102A43] border border-[#E7E2D8] dark:border-[#334155] rounded-xl px-4 py-3 text-center text-xl tracking-widest font-mono text-[#273444] dark:text-[#F1F5F9] placeholder-[#64748B] focus:outline-none focus:ring-2 focus:ring-[#B89B72] transition"
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={isVerifyingOtp || otpCode.length !== 6}
                    className="w-full py-3 px-4 rounded-xl font-bold text-sm bg-[#17324D] hover:bg-[#102A43] text-white transition shadow-sm flex items-center justify-center space-x-2 disabled:opacity-50"
                  >
                    {isVerifyingOtp ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin text-[#B89B72]" />
                        <span>Verifying & Signing In...</span>
                      </>
                    ) : (
                      <>
                        <CheckCircle2 className="w-4 h-4" />
                        <span>Verify & Sign In</span>
                      </>
                    )}
                  </button>
                </form>
              )}

              <div className="pt-2 border-t border-[#E7E2D8] dark:border-[#334155] text-center">
                <button
                  type="button"
                  onClick={() => {
                    setMode('login');
                    setError(null);
                  }}
                  className="inline-flex items-center space-x-1.5 text-xs text-[#64748B] dark:text-[#A8B3C2] hover:text-[#17324D] dark:hover:text-white transition"
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                  <span>Back to Standard Sign In</span>
                </button>
              </div>
            </div>
          )}

          {/* ════════════ 4. FORGOT PASSWORD / 2FA RESET ════════════ */}
          {mode === 'forgot-password' && (
            <div className="space-y-4 animate-in fade-in">
              <div className="flex items-center space-x-2 text-[#17324D] dark:text-[#D9C19A] bg-[#FAF8F3] dark:bg-[#102A43] border border-[#E7E2D8] dark:border-[#334155] p-3 rounded-xl">
                <KeyRound className="w-4 h-4 shrink-0 text-[#B89B72]" />
                <p className="text-xs text-[#64748B] dark:text-[#A8B3C2]">
                  {resetStep === 'request'
                    ? 'Enter your account email to receive a password reset verification code.'
                    : 'Enter the code and set your new password.'}
                </p>
              </div>

              {devCodeBanner && resetStep === 'verify' && (
                <div className="p-3 rounded-xl bg-emerald-500/10 border border-[#2E7D5B]/30 text-[#2E7D5B] text-xs flex items-center justify-between">
                  <span>Reset Code: <strong className="font-mono text-sm tracking-widest text-[#17324D] dark:text-white ml-1">{devCodeBanner}</strong></span>
                  <span className="text-[10px] bg-[#2E7D5B]/20 px-2 py-0.5 rounded text-[#2E7D5B] font-semibold">Active</span>
                </div>
              )}

              {/* Status Alert */}
              {resetStatus && (
                <div className={`p-3.5 rounded-xl border text-xs flex items-start gap-2.5 animate-in fade-in ${
                  resetStatus.success
                    ? 'bg-emerald-500/10 border-[#2E7D5B]/30 text-[#2E7D5B]'
                    : 'bg-rose-500/10 border-[#C75C5C]/30 text-[#C75C5C]'
                }`}>
                  {resetStatus.success ? (
                    <CheckCircle2 className="w-4 h-4 text-[#2E7D5B] shrink-0 mt-0.5" />
                  ) : (
                    <AlertCircle className="w-4 h-4 text-[#C75C5C] shrink-0 mt-0.5" />
                  )}
                  <span>{resetStatus.message}</span>
                </div>
              )}

              {resetStep === 'request' ? (
                <form onSubmit={handleSendResetOtp} className="space-y-4">
                  <div>
                    <label className="block text-xs font-semibold text-[#273444] dark:text-[#F1F5F9] mb-1.5">
                      Registered Email Address
                    </label>
                    <div className="relative">
                      <Mail className="w-4 h-4 text-[#64748B] dark:text-[#A8B3C2] absolute left-3.5 top-1/2 -translate-y-1/2" />
                      <input
                        type="email"
                        value={resetEmail}
                        onChange={(e) => setResetEmail(e.target.value)}
                        placeholder="student@university.edu"
                        required
                        className="w-full bg-[#FAF8F3] dark:bg-[#102A43] border border-[#E7E2D8] dark:border-[#334155] rounded-xl pl-10 pr-4 py-2.5 text-sm text-[#273444] dark:text-[#F1F5F9] placeholder-[#64748B] focus:outline-none focus:ring-2 focus:ring-[#B89B72] transition"
                      />
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={isResetting}
                    className="w-full py-3 px-4 rounded-xl font-bold text-sm bg-[#17324D] hover:bg-[#102A43] text-white transition shadow-sm flex items-center justify-center space-x-2 disabled:opacity-50"
                  >
                    {isResetting ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin text-[#B89B72]" />
                        <span>Sending Reset Code...</span>
                      </>
                    ) : (
                      <>
                        <KeyRound className="w-4 h-4" />
                        <span>Send Reset Code</span>
                      </>
                    )}
                  </button>
                </form>
              ) : (
                <form onSubmit={handleConfirmReset} className="space-y-4">
                  <div>
                    <label className="block text-xs font-semibold text-[#273444] dark:text-[#F1F5F9] mb-1.5">
                      6-Digit Reset Code
                    </label>
                    <input
                      type="text"
                      maxLength={6}
                      value={resetOtp}
                      onChange={(e) => setResetOtp(e.target.value.replace(/\D/g, ''))}
                      placeholder="123456"
                      required
                      className="w-full bg-[#FAF8F3] dark:bg-[#102A43] border border-[#E7E2D8] dark:border-[#334155] rounded-xl px-4 py-2.5 text-center tracking-widest font-mono text-base text-[#273444] dark:text-[#F1F5F9] placeholder-[#64748B] focus:outline-none focus:ring-2 focus:ring-[#B89B72] transition"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-[#273444] dark:text-[#F1F5F9] mb-1.5">
                      New Password (min 6 characters)
                    </label>
                    <div className="relative">
                      <Lock className="w-4 h-4 text-[#64748B] dark:text-[#A8B3C2] absolute left-3.5 top-1/2 -translate-y-1/2" />
                      <input
                        type={showNewPassword ? 'text' : 'password'}
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        placeholder="••••••••"
                        required
                        minLength={6}
                        className="w-full bg-[#FAF8F3] dark:bg-[#102A43] border border-[#E7E2D8] dark:border-[#334155] rounded-xl pl-10 pr-10 py-2.5 text-sm text-[#273444] dark:text-[#F1F5F9] placeholder-[#64748B] focus:outline-none focus:ring-2 focus:ring-[#B89B72] transition"
                      />
                      <button
                        type="button"
                        onClick={() => setShowNewPassword(!showNewPassword)}
                        className="absolute right-3.5 top-1/2 -translate-y-1/2 text-[#64748B] hover:text-[#273444] dark:hover:text-[#F1F5F9]"
                      >
                        {showNewPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-[#273444] dark:text-[#F1F5F9] mb-1.5">
                      Confirm New Password
                    </label>
                    <div className="relative">
                      <Lock className="w-4 h-4 text-[#64748B] dark:text-[#A8B3C2] absolute left-3.5 top-1/2 -translate-y-1/2" />
                      <input
                        type={showNewPassword ? 'text' : 'password'}
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        placeholder="••••••••"
                        required
                        minLength={6}
                        className="w-full bg-[#FAF8F3] dark:bg-[#102A43] border border-[#E7E2D8] dark:border-[#334155] rounded-xl pl-10 pr-4 py-2.5 text-sm text-[#273444] dark:text-[#F1F5F9] placeholder-[#64748B] focus:outline-none focus:ring-2 focus:ring-[#B89B72] transition"
                      />
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={isResetting}
                    className="w-full py-3 px-4 rounded-xl font-bold text-sm bg-[#17324D] hover:bg-[#102A43] text-white transition shadow-sm flex items-center justify-center space-x-2 disabled:opacity-50"
                  >
                    {isResetting ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin text-[#B89B72]" />
                        <span>Updating Password...</span>
                      </>
                    ) : (
                      <>
                        <CheckCircle2 className="w-4 h-4" />
                        <span>Verify Code & Reset Password</span>
                      </>
                    )}
                  </button>
                </form>
              )}

              <div className="pt-2 border-t border-[#E7E2D8] dark:border-[#334155] text-center">
                <button
                  type="button"
                  onClick={() => {
                    setMode('login');
                    setResetStatus(null);
                    setResetStep('request');
                  }}
                  className="inline-flex items-center space-x-1.5 text-xs text-[#64748B] dark:text-[#A8B3C2] hover:text-[#17324D] dark:hover:text-white transition"
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                  <span>Back to Sign In</span>
                </button>
              </div>
            </div>
          )}

        </div>

        {/* Security badge */}
        <div className="mt-6 flex items-center justify-center space-x-2 text-[11px] text-[#64748B] dark:text-[#A8B3C2]">
          <ShieldCheck className="w-4 h-4 text-[#2E7D5B]" />
          <span>2-Factor Authentication & Encrypted Session Active</span>
        </div>
      </div>
    </div>
  );
}
