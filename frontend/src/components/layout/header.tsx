'use client';

import { useEffect, useState } from 'react';
import { fetchHealthStatus } from '@/lib/api-client';
import { HealthStatus } from '@/lib/types';
import { Activity, ShieldCheck, Cpu } from 'lucide-react';

export default function Header() {
  const [health, setHealth] = useState<HealthStatus | null>(null);

  useEffect(() => {
    fetchHealthStatus().then(setHealth);
  }, []);

  return (
    <header className="h-16 border-b border-slate-800/80 bg-slate-950/50 backdrop-blur-md px-8 flex items-center justify-between sticky top-0 z-30">
      <div className="flex items-center space-x-4">
        <h2 className="text-sm font-semibold text-slate-300">
          Executive Career Guidance Engine
        </h2>
      </div>

      <div className="flex items-center space-x-6">
        {/* System Diagnostics Indicator */}
        <div className="flex items-center space-x-3 text-xs bg-slate-900/80 px-3 py-1.5 rounded-full border border-slate-800">
          <span className="flex items-center text-slate-400">
            <Cpu className="w-3.5 h-3.5 mr-1 text-indigo-400" />
            AI: <strong className="ml-1 text-slate-200 uppercase">{health?.ai_provider || 'Loading'}</strong>
          </span>
          <span className="text-slate-700">|</span>
          <span className="flex items-center text-slate-400">
            <Activity className="w-3.5 h-3.5 mr-1 text-emerald-400" />
            Backend: <strong className="ml-1 text-emerald-400">{health?.status === 'ok' ? 'Online' : 'Offline'}</strong>
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
