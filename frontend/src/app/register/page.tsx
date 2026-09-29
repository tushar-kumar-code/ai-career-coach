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
  Brain,
} from 'lucide-react';

export default function RegisterPage() {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isGoogleSubmitting, setIsGoogleSubmitting] = useState(false);

  const { register, loginWithGoogle, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, isLoading, router]);

  const handleGoogleRegister = async () => {
    setError(null);
    setIsGoogleSubmitting(true);
    try {
      await loginWithGoogle();
    } catch (err: any) {
      setError(err.message || 'Google registration failed. Please try again or use email.');
    } finally {
      setIsGoogleSubmitting(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password) {
      setError('Please fill in all required fields.');
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters long.');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match. Please re-enter.');
      return;
    }

    setError(null);
    setIsSubmitting(true);

    try {
      await register(email.trim(), password, fullName.trim() || undefined);
    } catch (err: any) {
      setError(err.message || 'Registration failed. Please try a different email.');
    } finally {
      setIsSubmitting(false);
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

          {/* Title & Subtitle */}
          <div className="text-center mb-7">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#17324D] dark:text-[#F1F5F9] tracking-tight">
              Create your account
            </h1>
            <p className="text-xs sm:text-sm text-[#64748B] dark:text-[#A8B3C2] mt-1.5">
              Start your journey towards your dream career.
            </p>
          </div>

          {/* Error Banner */}
          {error && (
            <div className="mb-5 p-3.5 rounded-xl bg-rose-500/10 border border-[#C75C5C]/30 text-[#C75C5C] text-xs flex items-start gap-2.5 animate-in fade-in">
              <AlertCircle className="w-4 h-4 text-[#C75C5C] shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {/* Registration Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-[#0F172A] dark:text-[#F1F5F9] mb-1.5">
                Full name
              </label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="e.g. Alex Johnson"
                className="w-full bg-white dark:bg-[#102A43] border border-[#E2E8F0] dark:border-[#334155] rounded-xl px-4 py-3 text-sm text-[#0F172A] dark:text-[#F1F5F9] placeholder-[#94A3B8] focus:outline-none focus:border-[#17324D] dark:focus:border-[#2563EB] transition"
              />
            </div>

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
                  placeholder="Create a password (min. 6 chars)"
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
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#0F172A] dark:text-[#F1F5F9] mb-1.5">
                Confirm password
              </label>
              <div className="relative">
                <input
                  type={showConfirmPassword ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Confirm your password"
                  required
                  className="w-full bg-white dark:bg-[#102A43] border border-[#E2E8F0] dark:border-[#334155] rounded-xl pl-4 pr-11 py-3 text-sm text-[#0F172A] dark:text-[#F1F5F9] placeholder-[#94A3B8] focus:outline-none focus:border-[#17324D] dark:focus:border-[#2563EB] transition"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-[#94A3B8] hover:text-[#0F172A] dark:hover:text-[#F1F5F9] p-1"
                >
                  {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Primary Create Account Button */}
            <button
              type="submit"
              disabled={isSubmitting || isGoogleSubmitting}
              className="w-full py-3.5 px-4 rounded-xl font-bold text-sm bg-[#17324D] hover:bg-[#102A43] text-white transition shadow-sm flex items-center justify-center space-x-2 disabled:opacity-50 mt-2 cursor-pointer"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-[#2563EB]" />
                  <span>Creating Account...</span>
                </>
              ) : (
                <span>Create account</span>
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
            onClick={handleGoogleRegister}
            disabled={isGoogleSubmitting || isSubmitting}
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

          {/* Footer Switch */}
          <div className="text-center pt-4 mt-4 border-t border-[#E2E8F0] dark:border-[#334155] text-xs text-[#64748B] dark:text-[#A8B3C2]">
            Already have an account?{' '}
            <Link
              href="/login"
              className="text-[#17324D] dark:text-[#38BDF8] font-bold hover:underline"
            >
              Log in
            </Link>
          </div>
        </div>
      </div>

      {/* Bottom Page Footer */}
      <footer className="w-full text-center py-5 text-xs text-[#64748B] dark:text-[#A8B3C2]">
        By creating an account, you agree to our{' '}
        <Link href="/" className="hover:underline text-[#0F172A] dark:text-[#F1F5F9]">Terms of Service</Link> and{' '}
        <Link href="/" className="hover:underline text-[#0F172A] dark:text-[#F1F5F9]">Privacy Policy</Link>.
      </footer>
    </div>
  );
}
