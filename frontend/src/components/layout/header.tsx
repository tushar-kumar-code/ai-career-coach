'use client';

import { useEffect, useState } from 'react';
import { fetchHealthStatus, getSavedAIConfig } from '@/lib/api-client';
import { HealthStatus } from '@/lib/types';
import { Activity, ShieldCheck, Menu, Sparkles, Key, Palette } from 'lucide-react';
import ApiKeyModal from '@/components/common/ApiKeyModal';
import ThemeModal from '@/components/common/ThemeModal';
import { useTheme } from '@/context/ThemeContext';

interface HeaderProps {
  onOpenMobileMenu?: () => void;
}

export default function Header({ onOpenMobileMenu }: HeaderProps) {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [isKeyModalOpen, setIsKeyModalOpen] = useState(false);
  const [isThemeModalOpen, setIsThemeModalOpen] = useState(false);
  const { theme } = useTheme();
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
      <header className="h-16 border-b border-slate-800/80 bg-slate-950/60 backdrop-blur-md px-4 sm:px-6 lg:px-8 flex items-center justify-between sticky top-0 z-30 w-full">
        {/* Left: Mobile Hamburger Button & Title */}
        <div className="flex items-center space-x-3 sm:space-x-4">
          {onOpenMobileMenu && (
            <button
              onClick={onOpenMobileMenu}
              aria-label="Open navigation menu"
              className="lg:hidden p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:bg-slate-800 transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
            >
              <Menu className="w-5 h-5" />
            </button>
          )}

          <div className="flex items-center space-x-2">
            <div className="lg:hidden w-7 h-7 rounded-lg bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center text-white shadow-sm">
              <Sparkles className="w-4 h-4" />
            </div>
            <h2 className="text-xs sm:text-sm font-semibold text-slate-200 truncate max-w-[200px] sm:max-w-none">
              AI Career Coach Cockpit
            </h2>
          </div>
        </div>

        {/* Right: Theme Switcher, API Key Trigger & Diagnostics */}
        <div className="flex items-center space-x-2 sm:space-x-2.5">
          {/* Quick Theme Switcher Button */}
          <button
            onClick={() => setIsThemeModalOpen(true)}
            className="flex items-center space-x-1.5 text-xs px-2.5 sm:px-3 py-1.5 rounded-full border border-slate-800 bg-slate-900/80 hover:bg-slate-800 text-slate-300 hover:text-white transition font-medium shadow-sm"
            title="Change Theme & Appearance"
          >
            <Palette className="w-3.5 h-3.5 text-indigo-400" />
            <span className="hidden sm:inline capitalize">{theme}</span>
          </button>

          {/* AI Key Config Button */}
          <button
            onClick={() => setIsKeyModalOpen(true)}
            className={`flex items-center space-x-1.5 text-xs px-3 py-1.5 rounded-full border transition font-medium shadow-sm ${
              activeKeyProvider.hasKey
                ? 'bg-indigo-600/15 border-indigo-500/40 text-indigo-300 hover:bg-indigo-600/25'
                : 'bg-amber-500/10 border-amber-500/30 text-amber-300 hover:bg-amber-500/20'
            }`}
            title="Configure your personal AI API Key"
          >
            <Key className="w-3.5 h-3.5" />
            <span className="hidden xs:inline">
              {activeKeyProvider.hasKey ? (
                <>AI: <span className="uppercase font-bold text-white">{activeKeyProvider.provider}</span> (Active)</>
              ) : (
                <>Set AI Key</>
              )}
            </span>
          </button>

          {/* Diagnostics Status Badges */}
          <div className="hidden md:flex items-center space-x-2 sm:space-x-3 text-xs bg-slate-900/80 px-2.5 sm:px-3 py-1.5 rounded-full border border-slate-800">
            <span className="flex items-center text-slate-400">
              <Activity className="w-3.5 h-3.5 mr-1 text-emerald-400" />
              <strong className="text-emerald-400">{health?.status === 'ok' ? 'Online' : 'Connected'}</strong>
            </span>
            <span className="text-slate-700">|</span>
            <span className="flex items-center text-slate-400">
              <ShieldCheck className="w-3.5 h-3.5 mr-1 text-sky-400" />
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
