'use client';

import { useEffect, useState } from 'react';
import { fetchHealthStatus } from '@/lib/api-client';
import { HealthStatus } from '@/lib/types';
import { Activity, ShieldCheck, Cpu, Menu, Sparkles } from 'lucide-react';

interface HeaderProps {
  onOpenMobileMenu?: () => void;
}

export default function Header({ onOpenMobileMenu }: HeaderProps) {
  const [health, setHealth] = useState<HealthStatus | null>(null);

  useEffect(() => {
    fetchHealthStatus().then(setHealth).catch(() => {});
  }, []);

  return (
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

      {/* Right: Diagnostics & Status Badges */}
      <div className="flex items-center space-x-3 sm:space-x-4">
        <div className="flex items-center space-x-2 sm:space-x-3 text-xs bg-slate-900/80 px-2.5 sm:px-3 py-1.5 rounded-full border border-slate-800">
          <span className="hidden sm:inline-flex items-center text-slate-400">
            <Cpu className="w-3.5 h-3.5 mr-1 text-indigo-400" />
            AI: <strong className="ml-1 text-slate-200 uppercase">{health?.ai_provider || 'Active'}</strong>
          </span>
          <span className="hidden sm:inline text-slate-700">|</span>
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
  );
}
