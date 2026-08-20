'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  LayoutDashboard, 
  Compass, 
  FileText, 
  Award, 
  Briefcase, 
  MapPin, 
  Mic, 
  TrendingUp, 
  MessageSquare,
  Sparkles
} from 'lucide-react';

const NAV_ITEMS = [
  { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { label: 'Discovery Assessment', href: '/assessment', icon: Compass },
  { label: 'Digital Twin Profile', href: '/profile', icon: Sparkles },
  { label: 'Resume & ATS', href: '/resume', icon: FileText },
  { label: 'Skill Matrix', href: '/skills', icon: Award },
  { label: 'Job Engine', href: '/jobs', icon: Briefcase },
  { label: 'Roadmap & Tasks', href: '/roadmap', icon: MapPin },
  { label: 'Mock Interview', href: '/interview', icon: Mic },
  { label: 'Progress & Readiness', href: '/progress', icon: TrendingUp },
  { label: 'AI Career Coach', href: '/chat', icon: MessageSquare },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-950/80 backdrop-blur-xl flex flex-col h-screen fixed left-0 top-0 z-40">
      {/* Brand Header */}
      <div className="p-6 border-b border-slate-800/60 flex items-center space-x-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
          <Sparkles className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="font-bold text-lg text-white leading-tight">AI Career Coach</h1>
          <p className="text-xs text-slate-400 font-medium">Personal Twin Platform</p>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 overflow-y-auto p-4 space-y-1">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center space-x-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                isActive
                  ? 'bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-indigo-400' : 'text-slate-400'}`} />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Footer User Widget */}
      <div className="p-4 border-t border-slate-800/60">
        <div className="flex items-center space-x-3 p-2 rounded-lg bg-slate-900/40 border border-slate-800/40">
          <div className="w-8 h-8 rounded-full bg-gradient-to-r from-purple-500 to-indigo-500 flex items-center justify-center text-xs font-bold text-white">
            CC
          </div>
          <div className="overflow-hidden">
            <p className="text-xs font-semibold text-slate-200 truncate">Career Discovery User</p>
            <p className="text-[10px] text-slate-500 truncate">Pro Account Active</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
