'use client';

import { useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import Sidebar from '@/components/layout/sidebar';
import Header from '@/components/layout/header';
import FirstTimeApiKeyModal from '@/components/common/FirstTimeApiKeyModal';
import GlobalAIAssistant from '@/components/chat/GlobalAIAssistant';
import { Loader2, Sparkles, Compass } from 'lucide-react';
import { getSavedAIConfig } from '@/lib/api-client';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [showApiKeyModal, setShowApiKeyModal] = useState(false);
  const { isAuthenticated, isLoading, hasCompletedAssessment } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace('/login');
    }
  }, [isAuthenticated, isLoading, router]);

  // Assessment Gate: Strictly restrict unassessed users to /assessment only.
  // No other feature can be viewed or accessed until the assessment is completed.
  useEffect(() => {
    if (!isLoading && isAuthenticated && !hasCompletedAssessment) {
      if (pathname !== '/assessment') {
        router.replace('/assessment');
      }
    }
  }, [isLoading, isAuthenticated, hasCompletedAssessment, pathname, router]);

  // After login, check if API key is configured — show modal once if not
  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      const dismissed = sessionStorage.getItem('api_key_modal_dismissed');
      if (dismissed) return;

      const config = getSavedAIConfig();
      if (!config.apiKey) {
        // Small delay so dashboard renders first
        const timer = setTimeout(() => setShowApiKeyModal(true), 800);
        return () => clearTimeout(timer);
      }
    }
  }, [isAuthenticated, isLoading]);

  const handleApiKeyModalClose = () => {
    setShowApiKeyModal(false);
    sessionStorage.setItem('api_key_modal_dismissed', '1');
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center space-y-4">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-lg shadow-indigo-500/25 animate-pulse">
          <Sparkles className="w-6 h-6 text-white" />
        </div>
        <div className="flex items-center space-x-2 text-xs text-slate-400">
          <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
          <span>Authenticating Candidate Session...</span>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col lg:flex-row w-full overflow-x-hidden">
      <Sidebar
        isMobileOpen={mobileMenuOpen}
        onClose={() => setMobileMenuOpen(false)}
      />

      <div className="flex-1 lg:ml-64 flex flex-col min-h-screen w-full min-w-0">
        <Header onOpenMobileMenu={() => setMobileMenuOpen(true)} />
        <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto overflow-x-hidden">
          {!hasCompletedAssessment && pathname !== '/assessment' && (
            <div className="mb-6 p-4 rounded-xl bg-gradient-to-r from-indigo-950/80 via-purple-950/60 to-slate-900 border border-indigo-500/30 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center shrink-0">
                  <Compass className="w-5 h-5 animate-pulse" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-white">First Step Required: Complete Career Assessment</h4>
                  <p className="text-xs text-slate-300">
                    To give you personalized roadmap tasks, realistic job matches, and your real Career Digital Twin, you must take the assessment first.
                  </p>
                </div>
              </div>
              <Link
                href="/assessment"
                className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shrink-0 transition shadow-lg shadow-indigo-600/30"
              >
                Go to Assessment 🎯
              </Link>
            </div>
          )}
          {children}
        </main>
      </div>

      {/* One-time post-login API Key setup modal */}
      <FirstTimeApiKeyModal
        isOpen={showApiKeyModal}
        onClose={handleApiKeyModalClose}
        onSkip={handleApiKeyModalClose}
      />

      {/* Unified Context-Aware Global AI Assistant Drawer & FAB */}
      <GlobalAIAssistant />
    </div>
  );
}
