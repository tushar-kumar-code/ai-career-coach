'use client';

import { useEffect, useState } from 'react';
import { fetchHealthStatus, getSavedAIConfig } from '@/lib/api-client';
import { HealthStatus } from '@/lib/types';
import { Activity, ShieldCheck, Menu, Sparkles, Key, Palette, Globe } from 'lucide-react';
import ApiKeyModal from '@/components/common/ApiKeyModal';
import ThemeModal from '@/components/common/ThemeModal';
import { useTheme } from '@/context/ThemeContext';
import { useLanguage } from '@/context/LanguageContext';

interface HeaderProps {
  onOpenMobileMenu?: () => void;
}

export default function Header({ onOpenMobileMenu }: HeaderProps) {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [isKeyModalOpen, setIsKeyModalOpen] = useState(false);
  const [isThemeModalOpen, setIsThemeModalOpen] = useState(false);
  const { theme } = useTheme();
  const { language, setLanguage, t } = useLanguage();
  const [activeKeyProvider, setActiveKeyProvider] = useState<{ provider: string; hasKey: boolean }>({
    provider: 'groq',
    hasKey: false,
  });

  const syncConfig = () => {
    const cfg = getSavedAIConfig();
    setActiveKeyProvider({
      provider: cfg.provider || 'groq',
      hasKey: !!cfg.apiKey,
    });
    fetchHealthStatus().then(setHealth).catch(() => {});
  };

  useEffect(() => {
    syncConfig();
    const handleUpdate = () => syncConfig();
    window.addEventListener('ai-config-updated', handleUpdate);
    return () => window.removeEventListener('ai-config-updated', handleUpdate);
  }, []);

  return (
    <>
      <header className="h-16 border-b border-slate-200 dark:border-slate-800/80 bg-white/95 dark:bg-[#162235]/95 backdrop-blur-md px-4 sm:px-6 lg:px-8 flex items-center justify-between sticky top-0 z-30 w-full">
        {/* Left: Mobile Hamburger Button & Title */}
        <div className="flex items-center space-x-3 sm:space-x-4">
          {onOpenMobileMenu && (
            <button
              onClick={onOpenMobileMenu}
              aria-label="Open navigation menu"
              className="lg:hidden p-2 rounded-xl bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-300 hover:text-[#17324D] dark:hover:text-white hover:bg-slate-200 dark:hover:bg-slate-800 transition-colors focus:outline-none focus:ring-2 focus:ring-[#247B7B]/50"
            >
              <Menu className="w-5 h-5" />
            </button>
          )}

          <div className="flex items-center space-x-2">
            <div className="lg:hidden w-7 h-7 rounded-lg bg-[#17324D] dark:bg-[#1E2D44] border border-[#247B7B]/40 flex items-center justify-center text-[#247B7B] dark:text-[#5FA8A8] shadow-sm">
              <Sparkles className="w-4 h-4" />
            </div>
            <h2 className="text-xs sm:text-sm font-semibold text-[#17324D] dark:text-slate-200 truncate max-w-[200px] sm:max-w-none">
              {t('header.cockpit', 'AI Career Coach Cockpit')}
            </h2>
          </div>
        </div>

        {/* Right: Language Switcher, Theme Switcher, API Key Trigger & Diagnostics */}
        <div className="flex items-center space-x-2 sm:space-x-2.5">
          {/* Quick Language Toggle Button */}
          <button
            onClick={() => setLanguage(language === 'en' ? 'hi' : 'en')}
            className="flex items-center space-x-1.5 text-xs px-2.5 sm:px-3 py-1.5 rounded-full border border-[#247B7B]/30 bg-[#247B7B]/10 hover:bg-[#247B7B]/20 text-[#247B7B] dark:text-[#5FA8A8] transition font-semibold shadow-sm"
            title="Switch Language (English / Hindi)"
          >
            <Globe className="w-3.5 h-3.5 text-[#247B7B] dark:text-[#5FA8A8]" />
            <span>{language === 'en' ? 'EN' : 'हिंदी'}</span>
          </button>

          {/* Quick Theme Switcher Button */}
          <button
            onClick={() => setIsThemeModalOpen(true)}
            className="flex items-center space-x-1.5 text-xs px-2.5 sm:px-3 py-1.5 rounded-full border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/80 hover:bg-slate-100 dark:hover:bg-slate-800 text-[#17324D] dark:text-slate-300 transition font-medium shadow-sm"
            title="Change Theme & Appearance"
          >
            <Palette className="w-3.5 h-3.5 text-[#247B7B] dark:text-[#5FA8A8]" />
            <span className="hidden sm:inline capitalize">{theme}</span>
          </button>

          {/* AI Key Config Button */}
          <button
            onClick={() => setIsKeyModalOpen(true)}
            className={`flex items-center space-x-1.5 text-xs px-3 py-1.5 rounded-full border transition font-medium shadow-sm ${
              activeKeyProvider.hasKey
                ? 'bg-[#247B7B]/10 border-[#247B7B]/40 text-[#247B7B] dark:text-[#5FA8A8] hover:bg-[#247B7B]/20'
                : 'bg-[#C78A20]/10 border-[#C78A20]/30 text-[#C78A20] hover:bg-[#C78A20]/20'
            }`}
            title="Configure your personal AI API Key"
          >
            <Key className="w-3.5 h-3.5" />
            <span className="hidden xs:inline">
              {activeKeyProvider.hasKey ? (
                <>AI: <span className="uppercase font-bold text-[#17324D] dark:text-white">{activeKeyProvider.provider}</span> ({t('header.activeKey', 'Active')})</>
              ) : (
                <>{t('header.setAiKey', 'Set AI Key')}</>
              )}
            </span>
          </button>

          {/* Diagnostics Status Badges */}
          <div className="hidden md:flex items-center space-x-2 sm:space-x-3 text-xs bg-slate-100 dark:bg-slate-900/80 px-2.5 sm:px-3 py-1.5 rounded-full border border-slate-200 dark:border-slate-800">
            <span className="flex items-center text-slate-500 dark:text-slate-400">
              <Activity className="w-3.5 h-3.5 mr-1 text-[#2E7D5B]" />
              <strong className="text-[#2E7D5B]">{health?.status === 'ok' ? t('header.online', 'Online') : t('header.connected', 'Connected')}</strong>
            </span>
            <span className="text-slate-300 dark:text-slate-700">|</span>
            <span className="flex items-center text-slate-500 dark:text-slate-400">
              <ShieldCheck className="w-3.5 h-3.5 mr-1 text-[#247B7B] dark:text-[#5FA8A8]" />
              v{health?.version || '1.0'}
            </span>
          </div>
        </div>
      </header>

      {/* API Key Modal */}
      <ApiKeyModal
        isOpen={isKeyModalOpen}
        onClose={() => setIsKeyModalOpen(false)}
        onSaved={syncConfig}
      />

      {/* Theme Customization Modal */}
      <ThemeModal
        isOpen={isThemeModalOpen}
        onClose={() => setIsThemeModalOpen(false)}
      />
    </>
  );
}
