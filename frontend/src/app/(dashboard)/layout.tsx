'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import Sidebar from '@/components/layout/sidebar';
import Header from '@/components/layout/header';
import FirstTimeApiKeyModal from '@/components/common/FirstTimeApiKeyModal';
import { Loader2, Sparkles } from 'lucide-react';
import { getSavedAIConfig } from '@/lib/api-client';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [showApiKeyModal, setShowApiKeyModal] = useState(false);
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace('/login');
    }
  }, [isAuthenticated, isLoading, router]);

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
          {children}
        </main>
      </div>

      {/* One-time post-login API Key setup modal */}
      <FirstTimeApiKeyModal
        isOpen={showApiKeyModal}
        onClose={handleApiKeyModalClose}
        onSkip={handleApiKeyModalClose}
      />
    </div>
  );
}
