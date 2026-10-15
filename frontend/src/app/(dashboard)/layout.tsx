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
  const { isAuthenticated, isLoading, isAnalyzed } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace('/login');
    }
  }, [isAuthenticated, isLoading, router]);

  // Allowed onboarding routes when user profile is not yet analyzed
  const isAllowedOnboardingRoute = pathname === '/resume' || pathname === '/assessment';

  // If user is authenticated but hasn't completed analysis, redirect if on locked route
  useEffect(() => {
    if (!isLoading && isAuthenticated && !isAnalyzed && !isAllowedOnboardingRoute) {
      router.replace('/resume');
    }
  }, [isAuthenticated, isLoading, isAnalyzed, isAllowedOnboardingRoute, router]);

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

  // If user hasn't completed analysis and tries to access other features, lock visibility completely
  const isFeatureLocked = !isAnalyzed && !isAllowedOnboardingRoute;

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
            <div className="flex flex-col items-center justify-center min-h-[65vh] text-center p-4 sm:p-6 animate-in fade-in duration-300">
              <div className="max-w-xl w-full p-6 sm:p-8 rounded-3xl bg-white dark:bg-[#1E293B] border border-blue-500/30 shadow-2xl space-y-6">
                <div className="w-16 h-16 mx-auto rounded-2xl bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-600 dark:text-sky-400 shadow-sm">
                  <Lock className="w-8 h-8 animate-pulse" />
                </div>
                
                <div className="space-y-2">
                  <h3 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-white">
                    Profile Analysis Required
                  </h3>
                  <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-300 leading-relaxed font-normal">
                    Jab tak application aapko analysis na kar le, baki koi bhi feature visible nahi hoga. Aap Resume upload karke instant analysis pa sakte hain ya Career Discovery Assessment de sakte hain.
                  </p>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 text-left">
                  {/* Option 1: Resume */}
                  <Link
                    href="/resume"
                    className="p-5 rounded-2xl border border-blue-500/40 bg-blue-50/50 dark:bg-blue-950/20 hover:border-blue-500 hover:bg-blue-100/50 dark:hover:bg-blue-900/30 transition-all flex flex-col justify-between group space-y-4 shadow-sm"
                  >
                    <div className="space-y-2">
                      <div className="inline-flex items-center space-x-1.5 px-2 py-0.5 rounded-md bg-blue-600/10 text-blue-600 dark:text-sky-400 text-[11px] font-bold uppercase tracking-wider">
                        <span>Option 1 (Fastest)</span>
                      </div>
                      <h4 className="text-sm font-bold text-slate-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-sky-400 transition-colors">
                        Upload Resume
                      </h4>
                      <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                        Apna resume upload karein. AI 30 seconds me skills aur profile analyze karke baki sabhi features unlock kar dega.
                      </p>
                    </div>
                    <div className="inline-flex items-center space-x-1 text-xs font-semibold text-blue-600 dark:text-sky-400">
                      <span>Upload Resume Now</span>
                      <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
                    </div>
                  </Link>

                  {/* Option 2: Assessment */}
                  <Link
                    href="/assessment"
                    className="p-5 rounded-2xl border border-indigo-500/40 bg-indigo-50/50 dark:bg-indigo-950/20 hover:border-indigo-500 hover:bg-indigo-100/50 dark:hover:bg-indigo-900/30 transition-all flex flex-col justify-between group space-y-4 shadow-sm"
                  >
                    <div className="space-y-2">
                      <div className="inline-flex items-center space-x-1.5 px-2 py-0.5 rounded-md bg-indigo-600/10 text-indigo-600 dark:text-indigo-400 text-[11px] font-bold uppercase tracking-wider">
                        <span>Option 2 (Interactive)</span>
                      </div>
                      <h4 className="text-sm font-bold text-slate-900 dark:text-white group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                        Career Assessment
                      </h4>
                      <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                        Discovery questions ka answer dekar apni career personality aur skills analyze karein.
                      </p>
                    </div>
                    <div className="inline-flex items-center space-x-1 text-xs font-semibold text-indigo-600 dark:text-indigo-400">
                      <span>Start Assessment</span>
                      <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
                    </div>
                  </Link>
                </div>
              </div>
            </div>
          ) : (
            children
          )}
        </main>
      </div>

      {/* Global AI Assistant Drawer & FAB (Unlocked only after user is analyzed) */}
      {isAnalyzed && <GlobalAIAssistant />}
    </div>
  );
}
