'use client';

import Link from 'next/link';
import { GraduationCap, TrendingUp, Sparkles } from 'lucide-react';

interface CareerHubTabsProps {
  activeTab: 'placement' | 'progress' | 'profile';
}

const TABS = [
  {
    id: 'placement',
    label: 'Placement Readiness',
    sublabel: 'Campus Audit & Checklist',
    href: '/placement',
    icon: GraduationCap,
  },
  {
    id: 'progress',
    label: 'Progress & Twin',
    sublabel: 'Readiness History & Reports',
    href: '/progress',
    icon: TrendingUp,
  },
  {
    id: 'profile',
    label: 'Digital Twin Profile',
    sublabel: 'Live Signals & Skill Matrix',
    href: '/profile',
    icon: Sparkles,
  },
] as const;

export default function CareerHubTabs({ activeTab }: CareerHubTabsProps) {
  return (
    <div className="w-full mb-6">
      <div className="p-1.5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-md flex flex-col sm:flex-row gap-1.5">
        {TABS.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <Link
              key={tab.id}
              href={tab.href}
              className={`flex-1 flex items-center space-x-3 px-4 py-3 rounded-xl transition-all min-h-[44px] ${
                isActive
                  ? 'bg-gradient-to-r from-indigo-600 to-violet-600 text-white shadow-lg shadow-indigo-600/25'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <div
                className={`p-2 rounded-lg shrink-0 ${
                  isActive ? 'bg-white/15 text-white' : 'bg-slate-800 text-slate-400'
                }`}
              >
                <Icon className="w-4 h-4" />
              </div>
              <div className="text-left overflow-hidden">
                <div className="text-xs font-bold truncate leading-tight">{tab.label}</div>
                <div
                  className={`text-[10px] truncate ${
                    isActive ? 'text-indigo-100' : 'text-slate-500'
                  }`}
                >
                  {tab.sublabel}
                </div>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
