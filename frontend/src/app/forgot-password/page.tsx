'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  Sparkles,
  Lock,
  Mail,
  Eye,
  EyeOff,
  Loader2,
  AlertCircle,
  ShieldCheck,
  CheckCircle2,
  KeyRound,
  ArrowLeft,
} from 'lucide-react';
import { resetPassword } from '@/lib/api-client';

export default function ForgotPasswordPage() {
  const [resetEmail, setResetEmail] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [resetStatus, setResetStatus] = useState<{ success: boolean; message: string } | null>(null);
  const [isResetting, setIsResetting] = useState(false);
  const router = useRouter();

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setResetStatus(null);

    if (!resetEmail.trim()) {
      setResetStatus({ success: false, message: 'Please enter your registered email address.' });
      return;
    }

    if (!newPassword || newPassword.length < 6) {
      setResetStatus({ success: false, message: 'New password must be at least 6 characters.' });
      return;
    }

    if (newPassword !== confirmPassword) {
      setResetStatus({ success: false, message: 'New password and confirm password do not match.' });
      return;
    }

    setIsResetting(true);
    try {
      const res = await resetPassword(resetEmail.trim(), newPassword);
      setResetStatus({
        success: true,
        message: res.message || 'Password reset successfully! Redirecting to Sign In...',
      });
      setTimeout(() => {
        router.push('/login');
      }, 1800);
    } catch (err: any) {
      setResetStatus({
        success: false,
        message: err.message || 'Failed to reset password. Please verify the email address exists.',
      });
    } finally {
      setIsResetting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC] dark:bg-[#0F172A] text-[#0F172A] dark:text-[#F1F5F9] flex flex-col justify-center items-center p-4 sm:p-6 relative selection:bg-blue-600 selection:text-white">
      {/* Main Container */}
      <div className="relative w-full max-w-md">
        {/* Brand Header */}
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center space-x-3 group mb-4">
            <div className="w-12 h-12 rounded-2xl bg-[#17324D] dark:bg-[#102A43] border border-[#2563EB]/40 flex items-center justify-center shadow-sm group-hover:scale-105 transition">
              <Sparkles className="w-6 h-6 text-[#2563EB]" />
            </div>
            <span className="font-extrabold text-2xl text-[#17324D] dark:text-[#F1F5F9] tracking-tight">AI Career Coach</span>
          </Link>
          <h1 className="text-xl sm:text-2xl font-bold text-[#17324D] dark:text-[#F1F5F9] tracking-tight">
            Reset Your Password
          </h1>
          <p className="text-xs sm:text-sm text-[#64748B] dark:text-[#A8B3C2] mt-1">
            Enter your account email and choose a new password
          </p>
        </div>

        {/* Card */}
        <div className="p-6 sm:p-8 rounded-3xl bg-white dark:bg-[#172235] border border-[#E2E8F0] dark:border-[#334155] shadow-sm space-y-6">
          <div className="flex items-center space-x-2 text-[#17324D] dark:text-[#38BDF8] bg-[#F8FAFC] dark:bg-[#102A43] border border-[#E2E8F0] dark:border-[#334155] p-3 rounded-xl">
            <KeyRound className="w-4 h-4 shrink-0 text-[#2563EB]" />
            <p className="text-xs text-[#64748B] dark:text-[#A8B3C2]">
              Enter your registered email address to set a new password.
            </p>
          </div>

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

          <form onSubmit={handleResetPassword} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-[#0F172A] dark:text-[#F1F5F9] mb-1.5">
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
                  className="w-full bg-[#F8FAFC] dark:bg-[#102A43] border border-[#E2E8F0] dark:border-[#334155] rounded-xl pl-10 pr-4 py-2.5 text-sm text-[#0F172A] dark:text-[#F1F5F9] placeholder-[#64748B] focus:outline-none focus:ring-2 focus:ring-[#2563EB] transition"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#0F172A] dark:text-[#F1F5F9] mb-1.5">
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
                  className="w-full bg-[#F8FAFC] dark:bg-[#102A43] border border-[#E2E8F0] dark:border-[#334155] rounded-xl pl-10 pr-10 py-2.5 text-sm text-[#0F172A] dark:text-[#F1F5F9] placeholder-[#64748B] focus:outline-none focus:ring-2 focus:ring-[#2563EB] transition"
                />
                <button
                  type="button"
                  onClick={() => setShowNewPassword(!showNewPassword)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-[#64748B] hover:text-[#0F172A] dark:hover:text-[#F1F5F9]"
                >
                  {showNewPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#0F172A] dark:text-[#F1F5F9] mb-1.5">
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
                  className="w-full bg-[#F8FAFC] dark:bg-[#102A43] border border-[#E2E8F0] dark:border-[#334155] rounded-xl pl-10 pr-4 py-2.5 text-sm text-[#0F172A] dark:text-[#F1F5F9] placeholder-[#64748B] focus:outline-none focus:ring-2 focus:ring-[#2563EB] transition"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isResetting}
              className="w-full py-3 px-4 rounded-xl font-bold text-sm bg-[#17324D] hover:bg-[#102A43] text-white transition shadow-sm flex items-center justify-center space-x-2 disabled:opacity-50 mt-2"
            >
              {isResetting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-[#2563EB]" />
                  <span>Updating Password...</span>
                </>
              ) : (
                <>
                  <KeyRound className="w-4 h-4" />
                  <span>Reset & Update Password</span>
                </>
              )}
            </button>
          </form>

          {/* Back to Login Button */}
          <div className="text-center pt-2 border-t border-[#E2E8F0] dark:border-[#334155]">
            <Link
              href="/login"
              className="inline-flex items-center space-x-1.5 text-xs text-[#64748B] dark:text-[#A8B3C2] hover:text-[#17324D] dark:hover:text-white transition"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to Sign In</span>
            </Link>
          </div>
        </div>

        {/* Security badge */}
        <div className="mt-6 flex items-center justify-center space-x-2 text-[11px] text-[#64748B] dark:text-[#A8B3C2]">
          <ShieldCheck className="w-4 h-4 text-[#2E7D5B]" />
          <span>Encrypted Session & JWT Authentication Enabled</span>
        </div>
      </div>
    </div>
  );
}
