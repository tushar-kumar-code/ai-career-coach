'use client';

import { useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { useLanguage } from '@/context/LanguageContext';
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
  Sparkles,
  Dumbbell,
  GraduationCap,
  LogOut,
  Settings,
  BookOpen,
  X
} from 'lucide-react';

const NAV_ITEMS = [
  { key: 'dashboard', label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { key: 'guide', label: 'How to Use', href: '/guide', icon: BookOpen },
  { key: 'assessment', label: 'Discovery Assessment', href: '/assessment', icon: Compass },
  { key: 'profile', label: 'Digital Twin Profile', href: '/profile', icon: Sparkles },
  { key: 'resume', label: 'Resume & ATS', href: '/resume', icon: FileText },
  { key: 'skills', label: 'Skill Matrix', href: '/skills', icon: Award },
  { key: 'jobs', label: 'Job Engine', href: '/jobs', icon: Briefcase },
  { key: 'roadmap', label: 'Roadmap & Tasks', href: '/roadmap', icon: MapPin },
  { key: 'practice', label: 'Micro Practice', href: '/practice', icon: Dumbbell },
  { key: 'interview', label: 'Mock Interview', href: '/interview', icon: Mic },
  { key: 'placement', label: 'Placement Readiness', href: '/placement', icon: GraduationCap },
  { key: 'progress', label: 'Progress & Readiness', href: '/progress', icon: TrendingUp },
  { key: 'chat', label: 'AI Career Coach', href: '/chat', icon: MessageSquare },
  { key: 'settings', label: 'Settings', href: '/settings', icon: Settings },
];

interface SidebarProps {
  isMobileOpen?: boolean;
  onClose?: () => void;
}

export default function Sidebar({ isMobileOpen = false, onClose }: SidebarProps) {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const { t } = useLanguage();

  // Close mobile drawer on Escape key press
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isMobileOpen && onClose) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isMobileOpen, onClose]);

  // Lock body scroll when mobile drawer is open
  useEffect(() => {
    if (isMobileOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isMobileOpen]);

  const initials = user?.full_name
    ? user.full_name
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    : user?.email
    ? user.email[0].toUpperCase()
    : 'CC';

  const renderNavLinks = () => (
    <nav className="flex-1 overflow-y-auto p-4 space-y-1">
      {NAV_ITEMS.map((item) => {
        const Icon = item.icon;
        const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
        const itemLabel = t(`nav.${item.key}`, item.label);
        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={() => {
              if (onClose) onClose();
            }}
            className={`flex items-center space-x-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
              isActive
                ? 'bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
            }`}
          >
            <Icon className={`w-4 h-4 ${isActive ? 'text-indigo-400' : 'text-slate-400'}`} />
            <span>{itemLabel}</span>
          </Link>
        );
      })}
    </nav>
  );

  const renderFooter = () => (
    <div className="p-4 border-t border-slate-800/60 space-y-2">
      <div className="flex items-center justify-between p-2 rounded-xl bg-slate-900/60 border border-slate-800/60">
        <div className="flex items-center space-x-2.5 overflow-hidden">
          <div className="w-8 h-8 rounded-full bg-gradient-to-r from-purple-500 to-indigo-500 flex items-center justify-center text-xs font-bold text-white shadow-sm shrink-0">
            {initials}
          </div>
          <div className="overflow-hidden">
            <p className="text-xs font-semibold text-slate-200 truncate">
              {user?.full_name || user?.email || 'Candidate'}
            </p>
            <p className="text-[10px] text-slate-400 truncate">{user?.email || t('nav.authenticatedAs', 'Candidate Account')}</p>
          </div>
        </div>

        <div className="flex items-center gap-1 shrink-0 ml-1">
          <Link
            href="/settings"
            onClick={() => { if (onClose) onClose(); }}
            title={t('nav.settings', 'Settings')}
            className="p-1.5 rounded-lg text-slate-400 hover:text-indigo-400 hover:bg-indigo-500/10 transition"
          >
            <Settings className="w-4 h-4" />
          </Link>
          <button
            onClick={logout}
            title={t('nav.signOut', 'Sign Out')}
            className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* 1. Desktop Fixed Sidebar */}
      <aside className="hidden lg:flex w-64 border-r border-slate-800 bg-slate-950/80 backdrop-blur-xl flex-col h-screen fixed left-0 top-0 z-40">
        {/* Brand Header */}
        <div className="p-6 border-b border-slate-800/60 flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-lg text-white leading-tight">{t('app.title', 'AI Career Coach')}</h1>
            <p className="text-xs text-slate-400 font-medium">{t('nav.brandSubtitle', 'Personal Twin Platform')}</p>
          </div>
        </div>


        {renderNavLinks()}
        {renderFooter()}
      </aside>

      {/* 2. Mobile / Tablet Off-Canvas Drawer */}
      {isMobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          {/* Backdrop Overlay */}
          <div 
            className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm transition-opacity duration-300 animate-in fade-in"
            onClick={onClose}
            aria-hidden="true"
          />

          {/* Slide-in Drawer */}
          <div 
            className="fixed inset-y-0 left-0 w-72 max-w-[85vw] bg-slate-950 border-r border-slate-800 flex flex-col z-50 shadow-2xl transition-transform duration-300 ease-out animate-in slide-in-from-left"
            role="dialog"
            aria-modal="true"
            aria-label="Navigation Menu"
          >
            {/* Drawer Header */}
            <div className="p-5 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center shadow-md">
                  <Sparkles className="w-4 h-4 text-white" />
                </div>
                <span className="font-bold text-base text-white">AI Career Coach</span>
              </div>
              <button
                onClick={onClose}
                aria-label="Close navigation menu"
                className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {renderNavLinks()}
            {renderFooter()}
          </div>
        </div>
      )}
    </>
  );
}
