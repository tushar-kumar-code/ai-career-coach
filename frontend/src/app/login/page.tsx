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

  const { login, demoLogin, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, isLoading, router]);

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
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-center items-center p-4 sm:p-6 relative overflow-hidden selection:bg-indigo-500 selection:text-white">
      {/* Ambient glows */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-indigo-600/15 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-10 right-10 w-80 h-80 bg-purple-600/10 rounded-full blur-3xl pointer-events-none" />

      {/* Main Container */}
      <div className="relative w-full max-w-md">
        {/* Brand Header */}
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center space-x-3 group mb-4">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-lg shadow-indigo-500/25 group-hover:scale-105 transition">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <span className="font-extrabold text-2xl text-white tracking-tight">AI Career Coach</span>
          </Link>

          <h1 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
            {mode === 'login' && 'Sign in to Career Cockpit'}
            {mode === 'otp-login' && '2-Factor / OTP Quick Sign In'}
            {mode === 'another-ways' && 'Choose How to Sign In'}
            {mode === 'forgot-password' && 'Reset Your Password'}
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            {mode === 'login' && 'Access your digital twin, roadmap & mock interviews'}
            {mode === 'otp-login' && 'Sign in instantly with a 6-digit verification code'}
            {mode === 'another-ways' && 'Select your preferred verification method'}
            {mode === 'forgot-password' && 'Verify your identity and set a new password'}
          </p>
        </div>

        {/* Card */}
        <div className="p-6 sm:p-8 rounded-3xl bg-slate-900/80 border border-slate-800 shadow-2xl backdrop-blur-xl space-y-6">

          {/* ════════════ 1. STANDARD LOGIN ════════════ */}
          {mode === 'login' && (
            <>
              {/* 1-Click Demo Login */}
              <div className="p-3.5 rounded-2xl bg-gradient-to-r from-indigo-500/10 via-purple-500/10 to-pink-500/10 border border-indigo-500/20 text-center">
                <p className="text-xs text-slate-300 mb-2">Want a fast preview without typing?</p>
                <button
                  type="button"
                  onClick={handleDemoLogin}
                  disabled={isDemoSubmitting || isSubmitting}
                  className="w-full py-2.5 px-4 rounded-xl font-bold text-xs bg-indigo-600 hover:bg-indigo-500 text-white transition shadow-md shadow-indigo-600/25 flex items-center justify-center space-x-2 disabled:opacity-50"
                >
                  {isDemoSubmitting ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Logging in to Demo Account...</span>
                    </>
                  ) : (
                    <>
                      <Zap className="w-4 h-4 text-amber-300" />
                      <span>1-Click Instant Demo Login</span>
                    </>
                  )}
                </button>
              </div>

              <div className="flex items-center space-x-3 text-slate-600 text-xs uppercase font-semibold">
                <div className="flex-1 h-px bg-slate-800" />
                <span>Or Sign in with Email</span>
                <div className="flex-1 h-px bg-slate-800" />
              </div>

              {/* Error Alert */}
              {error && (
                <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-start gap-2.5 animate-in fade-in">
                  <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                  <span>{error}</span>
                </div>
              )}

              {/* Login Form */}
              <form onSubmit={handleLoginSubmit} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                    Email Address
                  </label>
                  <div className="relative">
                    <Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="student@university.edu"
                      required
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition"
                    />
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="text-xs font-semibold text-slate-300">
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
                      className="text-xs text-indigo-400 hover:text-indigo-300 hover:underline transition"
                    >
                      Forgot password?
                    </button>
                  </div>
                  <div className="relative">
                    <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••"
                      required
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-10 py-2.5 text-sm text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200"
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={isSubmitting || isDemoSubmitting}
                  className="w-full py-3 px-4 rounded-xl font-bold text-sm bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 hover:opacity-95 text-white transition shadow-lg shadow-indigo-500/25 flex items-center justify-center space-x-2 disabled:opacity-50 mt-2"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
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
                  className="inline-flex items-center space-x-1.5 text-xs text-indigo-400 hover:text-indigo-300 font-semibold transition hover:underline"
                >
                  <Fingerprint className="w-3.5 h-3.5" />
                  <span>Try another way to sign in (OTP / 2FA)</span>
                </button>
              </div>

              {/* Footer */}
              <div className="text-center pt-2 border-t border-slate-800/80 text-xs text-slate-400">
                Don&apos;t have an account yet?{' '}
                <Link
                  href="/register"
                  className="text-indigo-400 hover:text-indigo-300 font-semibold hover:underline"
                >
                  Create Account
                </Link>
              </div>
            </>
          )}

          {/* ════════════ 2. TRY ANOTHER WAY OPTIONS ════════════ */}
          {mode === 'another-ways' && (
            <div className="space-y-4 animate-in fade-in">
              <p className="text-xs text-slate-300">
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
                  className="w-full p-3.5 rounded-2xl bg-slate-950 border border-slate-800 hover:border-indigo-500/50 hover:bg-indigo-500/5 transition flex items-center space-x-3.5 text-left group"
                >
                  <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 shrink-0 group-hover:scale-105 transition">
                    <Smartphone className="w-5 h-5" />
                  </div>
                  <div className="flex-1">
                    <p className="text-xs font-bold text-white">6-Digit OTP / Verification Code</p>
                    <p className="text-[11px] text-slate-400">No password needed — instant one-time login code</p>
                  </div>
                  <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-indigo-400 transition" />
                </button>

                {/* Option B: 1-Click Instant Demo */}
                <button
                  type="button"
                  onClick={handleDemoLogin}
                  disabled={isDemoSubmitting}
                  className="w-full p-3.5 rounded-2xl bg-slate-950 border border-slate-800 hover:border-amber-500/50 hover:bg-amber-500/5 transition flex items-center space-x-3.5 text-left group"
                >
                  <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 shrink-0 group-hover:scale-105 transition">
                    <Zap className="w-5 h-5" />
                  </div>
                  <div className="flex-1">
                    <p className="text-xs font-bold text-white">1-Click Instant Candidate Demo</p>
                    <p className="text-[11px] text-slate-400">Instantly explore with pre-configured mock profile</p>
                  </div>
                  <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-amber-400 transition" />
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
                  className="w-full p-3.5 rounded-2xl bg-slate-950 border border-slate-800 hover:border-purple-500/50 hover:bg-purple-500/5 transition flex items-center space-x-3.5 text-left group"
                >
                  <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 shrink-0 group-hover:scale-105 transition">
                    <KeyRound className="w-5 h-5" />
                  </div>
                  <div className="flex-1">
                    <p className="text-xs font-bold text-white">Reset Forgotten Password</p>
                    <p className="text-[11px] text-slate-400">Set a new password using email verification</p>
                  </div>
                  <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-purple-400 transition" />
                </button>
              </div>

              <div className="pt-2 border-t border-slate-800 text-center">
                <button
                  type="button"
                  onClick={() => setMode('login')}
                  className="inline-flex items-center space-x-1.5 text-xs text-slate-400 hover:text-white transition"
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
              <div className="flex items-center space-x-2 text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 p-3 rounded-xl">
                <Smartphone className="w-4 h-4 shrink-0" />
                <p className="text-xs text-slate-300">
                  Enter your email address to receive a 6-digit security code for instant login.
                </p>
              </div>

              {/* Dev Code Quick Auto-Fill Banner */}
              {devCodeBanner && (
                <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center justify-between">
                  <span>Verification Code: <strong className="font-mono text-sm tracking-widest text-white ml-1">{devCodeBanner}</strong></span>
                  <span className="text-[10px] bg-emerald-500/20 px-2 py-0.5 rounded text-emerald-300 font-semibold">Active</span>
                </div>
              )}

              {error && (
                <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-start gap-2.5 animate-in fade-in">
                  <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                  <span>{error}</span>
                </div>
              )}

              {!otpSent ? (
                <form onSubmit={handleSendOtpLogin} className="space-y-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                      Your Email Address
                    </label>
                    <div className="relative">
                      <Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                      <input
                        type="email"
                        value={otpEmail}
                        onChange={(e) => setOtpEmail(e.target.value)}
                        placeholder="student@university.edu"
                        required
                        className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition"
                      />
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={isSendingOtp}
                    className="w-full py-3 px-4 rounded-xl font-bold text-sm bg-indigo-600 hover:bg-indigo-500 text-white transition shadow-lg shadow-indigo-500/25 flex items-center justify-center space-x-2 disabled:opacity-50"
                  >
                    {isSendingOtp ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
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
                      <label className="text-xs font-semibold text-slate-300">
                        Enter 6-Digit Code for <span className="text-indigo-400">{otpEmail}</span>
                      </label>
                      <button
                        type="button"
                        onClick={() => handleSendOtpLogin()}
                        disabled={isSendingOtp}
                        className="text-[11px] text-indigo-400 hover:underline flex items-center gap-1"
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
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-center text-xl tracking-widest font-mono text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition"
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={isVerifyingOtp || otpCode.length !== 6}
                    className="w-full py-3 px-4 rounded-xl font-bold text-sm bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 hover:opacity-95 text-white transition shadow-lg shadow-indigo-500/25 flex items-center justify-center space-x-2 disabled:opacity-50"
                  >
                    {isVerifyingOtp ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
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

              <div className="pt-2 border-t border-slate-800 text-center">
                <button
                  type="button"
                  onClick={() => {
                    setMode('login');
                    setError(null);
                  }}
                  className="inline-flex items-center space-x-1.5 text-xs text-slate-400 hover:text-white transition"
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
              <div className="flex items-center space-x-2 text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 p-3 rounded-xl">
                <KeyRound className="w-4 h-4 shrink-0" />
                <p className="text-xs text-slate-300">
                  {resetStep === 'request'
                    ? 'Enter your account email to receive a password reset verification code.'
                    : 'Enter the code and set your new password.'}
                </p>
              </div>

              {devCodeBanner && resetStep === 'verify' && (
                <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center justify-between">
                  <span>Reset Code: <strong className="font-mono text-sm tracking-widest text-white ml-1">{devCodeBanner}</strong></span>
                  <span className="text-[10px] bg-emerald-500/20 px-2 py-0.5 rounded text-emerald-300 font-semibold">Active</span>
                </div>
              )}

              {/* Status Alert */}
              {resetStatus && (
                <div className={`p-3.5 rounded-xl border text-xs flex items-start gap-2.5 animate-in fade-in ${
                  resetStatus.success
                    ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                    : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
                }`}>
                  {resetStatus.success ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                  ) : (
                    <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                  )}
                  <span>{resetStatus.message}</span>
                </div>
              )}

              {resetStep === 'request' ? (
                <form onSubmit={handleSendResetOtp} className="space-y-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                      Registered Email Address
                    </label>
                    <div className="relative">
                      <Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                      <input
                        type="email"
                        value={resetEmail}
                        onChange={(e) => setResetEmail(e.target.value)}
                        placeholder="student@university.edu"
                        required
                        className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition"
                      />
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={isResetting}
                    className="w-full py-3 px-4 rounded-xl font-bold text-sm bg-indigo-600 hover:bg-indigo-500 text-white transition shadow-lg shadow-indigo-500/25 flex items-center justify-center space-x-2 disabled:opacity-50"
                  >
                    {isResetting ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
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
                    <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                      6-Digit Reset Code
                    </label>
                    <input
                      type="text"
                      maxLength={6}
                      value={resetOtp}
                      onChange={(e) => setResetOtp(e.target.value.replace(/\D/g, ''))}
                      placeholder="123456"
                      required
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-center tracking-widest font-mono text-base text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                      New Password (min 6 characters)
                    </label>
                    <div className="relative">
                      <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                      <input
                        type={showNewPassword ? 'text' : 'password'}
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        placeholder="••••••••"
                        required
                        minLength={6}
                        className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-10 py-2.5 text-sm text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition"
                      />
                      <button
                        type="button"
                        onClick={() => setShowNewPassword(!showNewPassword)}
                        className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200"
                      >
                        {showNewPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                      Confirm New Password
                    </label>
                    <div className="relative">
                      <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                      <input
                        type={showNewPassword ? 'text' : 'password'}
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        placeholder="••••••••"
                        required
                        minLength={6}
                        className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition"
                      />
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={isResetting}
                    className="w-full py-3 px-4 rounded-xl font-bold text-sm bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 hover:opacity-95 text-white transition shadow-lg shadow-indigo-500/25 flex items-center justify-center space-x-2 disabled:opacity-50"
                  >
                    {isResetting ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
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

              <div className="pt-2 border-t border-slate-800 text-center">
                <button
                  type="button"
                  onClick={() => {
                    setMode('login');
                    setResetStatus(null);
                    setResetStep('request');
                  }}
                  className="inline-flex items-center space-x-1.5 text-xs text-slate-400 hover:text-white transition"
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                  <span>Back to Sign In</span>
                </button>
              </div>
            </div>
          )}

        </div>

        {/* Security badge */}
        <div className="mt-6 flex items-center justify-center space-x-2 text-[11px] text-slate-500">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>2-Factor Authentication & Encrypted Session Active</span>
        </div>
      </div>
    </div>
  );
}
