'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import {
  Sparkles,
  Lock,
  Mail,
  User,
  Eye,
  EyeOff,
  ArrowRight,
  Loader2,
  AlertCircle,
  ShieldCheck,
} from 'lucide-react';

export default function RegisterPage() {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
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
            Create your Candidate Account
          </h1>
          <p className="text-xs sm:text-sm text-[#64748B] dark:text-[#A8B3C2] mt-1">
            Start building your career digital twin, tailored roadmap & mock tests
          </p>
        </div>

        {/* Card */}
        <div className="p-6 sm:p-8 rounded-3xl bg-white dark:bg-[#172235] border border-[#E7E2D8] dark:border-[#334155] shadow-sm space-y-6">
          {/* Google Sign In Button */}
          <button
            type="button"
            onClick={handleGoogleRegister}
            disabled={isGoogleSubmitting || isSubmitting}
            className="w-full py-2.5 px-4 rounded-xl font-semibold text-xs bg-white dark:bg-[#102A43] hover:bg-[#FAF8F3] dark:hover:bg-[#172235] border border-[#E7E2D8] dark:border-[#334155] text-[#273444] dark:text-[#F1F5F9] transition flex items-center justify-center space-x-2.5 shadow-sm disabled:opacity-50"
          >
            {isGoogleSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-[#B89B72]" />
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

          <div className="flex items-center space-x-3 text-[#64748B] dark:text-[#A8B3C2] text-xs uppercase font-semibold">
            <div className="flex-1 h-px bg-[#E7E2D8] dark:bg-[#334155]" />
            <span>Or Register with Email</span>
            <div className="flex-1 h-px bg-[#E7E2D8] dark:bg-[#334155]" />
          </div>

          {/* Error Alert */}
          {error && (
            <div className="p-3.5 rounded-xl bg-rose-500/10 border border-[#C75C5C]/30 text-[#C75C5C] text-xs flex items-start gap-2.5 animate-in fade-in">
              <AlertCircle className="w-4 h-4 text-[#C75C5C] shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-[#273444] dark:text-[#F1F5F9] mb-1.5">
                Full Name
              </label>
              <div className="relative">
                <User className="w-4 h-4 text-[#64748B] dark:text-[#A8B3C2] absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="e.g. Alex Sharma"
                  className="w-full bg-[#FAF8F3] dark:bg-[#102A43] border border-[#E7E2D8] dark:border-[#334155] rounded-xl pl-10 pr-4 py-2.5 text-sm text-[#273444] dark:text-[#F1F5F9] placeholder-[#64748B] focus:outline-none focus:ring-2 focus:ring-[#B89B72] transition"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#273444] dark:text-[#F1F5F9] mb-1.5">
                Email Address <span className="text-[#C75C5C]">*</span>
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
              <label className="block text-xs font-semibold text-[#273444] dark:text-[#F1F5F9] mb-1.5">
                Password <span className="text-[#C75C5C]">*</span>
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-[#64748B] dark:text-[#A8B3C2] absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="At least 6 characters"
                  required
                  minLength={6}
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

            <div>
              <label className="block text-xs font-semibold text-[#273444] dark:text-[#F1F5F9] mb-1.5">
                Confirm Password <span className="text-[#C75C5C]">*</span>
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-[#64748B] dark:text-[#A8B3C2] absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Repeat your password"
                  required
                  className="w-full bg-[#FAF8F3] dark:bg-[#102A43] border border-[#E7E2D8] dark:border-[#334155] rounded-xl pl-10 pr-4 py-2.5 text-sm text-[#273444] dark:text-[#F1F5F9] placeholder-[#64748B] focus:outline-none focus:ring-2 focus:ring-[#B89B72] transition"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-3 px-4 rounded-xl font-bold text-sm bg-[#17324D] hover:bg-[#102A43] text-white transition shadow-sm flex items-center justify-center space-x-2 disabled:opacity-50 mt-2"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-[#B89B72]" />
                  <span>Creating Account...</span>
                </>
              ) : (
                <>
                  <span>Create Account</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Footer Link */}
          <div className="text-center pt-2 border-t border-[#E7E2D8] dark:border-[#334155] text-xs text-[#64748B] dark:text-[#A8B3C2]">
            Already have an account?{' '}
            <Link
              href="/login"
              className="text-[#17324D] dark:text-[#D9C19A] font-semibold hover:underline"
            >
              Sign In
            </Link>
          </div>
        </div>

        {/* Security badge */}
        <div className="mt-6 flex items-center justify-center space-x-2 text-[11px] text-[#64748B] dark:text-[#A8B3C2]">
          <ShieldCheck className="w-4 h-4 text-[#2E7D5B]" />
          <span>Firebase Encrypted Authentication & Secure Token Verification</span>
        </div>
      </div>
    </div>
  );
}
