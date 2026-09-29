'use client';

import { useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import Sidebar from '@/components/layout/sidebar';
import Header from '@/components/layout/header';
import GlobalAIAssistant from '@/components/chat/GlobalAIAssistant';
import { Loader2, Compass, ArrowRight, Lock } from 'lucide-react';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { isAuthenticated, isLoading, hasCompletedAssessment } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace('/login');
    }
  }, [isAuthenticated, isLoading, router]);

  // If user is authenticated but hasn't completed assessment, enforce redirect to /assessment
  useEffect(() => {
    if (!isLoading && isAuthenticated && !hasCompletedAssessment && pathname !== '/assessment') {
      router.replace('/assessment');
    }
  }, [isAuthenticated, isLoading, hasCompletedAssessment, pathname, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#F8FAFC] dark:bg-[#0F172A] text-[#0F172A] dark:text-[#F8FAFC] flex flex-col items-center justify-center space-y-4">
        <div className="w-12 h-12 rounded-2xl bg-white dark:bg-[#1E293B] border border-blue-500/30 flex items-center justify-center shadow-sm">
          <Compass className="w-6 h-6 text-blue-600 dark:text-sky-400 animate-pulse" />
        </div>
        <div className="flex items-center space-x-2 text-xs text-slate-700 dark:text-slate-300 font-medium">
          <Loader2 className="w-4 h-4 animate-spin text-blue-600 dark:text-sky-400" />
          <span>Authenticating Candidate Session...</span>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  // If user hasn't completed assessment and tries to access other features, lock visibility completely
  const isFeatureLocked = !hasCompletedAssessment && pathname !== '/assessment';

  return (
    <div className="min-h-screen bg-[#F8FAFC] dark:bg-[#0F172A] text-[#0F172A] dark:text-[#F8FAFC] flex flex-col lg:flex-row w-full overflow-x-hidden">
      <Sidebar
        isMobileOpen={mobileMenuOpen}
        onClose={() => setMobileMenuOpen(false)}
      />

      <div className="flex-1 lg:ml-64 flex flex-col min-h-screen w-full min-w-0">
        <Header onOpenMobileMenu={() => setMobileMenuOpen(true)} />
        <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto overflow-x-hidden">
          {isFeatureLocked ? (
            <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-6 animate-in fade-in duration-300">
              <div className="max-w-md w-full p-8 rounded-3xl bg-white dark:bg-[#1E293B] border border-blue-500/30 shadow-xl space-y-5">
                <div className="w-16 h-16 mx-auto rounded-2xl bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-600 dark:text-sky-400 shadow-sm">
                  <Lock className="w-8 h-8 animate-pulse" />
                </div>
                <div className="space-y-2">
                  <h3 className="text-xl font-bold text-slate-900 dark:text-white">
                    Discovery Assessment Required
                  </h3>
                  <p className="text-xs sm:text-sm text-slate-700 dark:text-slate-300 leading-relaxed font-normal">
                    Baaki sabhi features (Dashboard, Resume, Roadmap, Jobs, Mock Interviews) tab tak locked hain jab tak aap Career Discovery Assessment complete nahi kar lete.
                  </p>
                </div>
                <div className="pt-2">
                  <Link
                    href="/assessment"
                    className="inline-flex items-center justify-center gap-2 w-full py-3.5 px-4 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold text-sm transition shadow-lg shadow-blue-500/20 min-h-[44px]"
                  >
                    <Compass className="w-4 h-4" />
                    <span>Complete Discovery Assessment Now</span>
                    <ArrowRight className="w-4 h-4" />
                  </Link>
                </div>
              </div>
            </div>
          ) : (
            children
          )}
        </main>
      </div>

      {/* Unified Context-Aware Global AI Assistant Drawer & FAB (Unlocked only after assessment) */}
      {hasCompletedAssessment && <GlobalAIAssistant />}
    </div>
  );
}
