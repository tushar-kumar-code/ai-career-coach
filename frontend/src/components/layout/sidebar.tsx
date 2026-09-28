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
  X,
  Lock
} from 'lucide-react';

interface NavItemConfig {
  key: string;
  label: string;
  href: string;
  icon: React.ElementType;
  step?: string;
}

interface NavGroupConfig {
  group: string;
  title?: string;
  items: NavItemConfig[];
}

const NAV_GROUPS: NavGroupConfig[] = [
  {
    group: 'overview',
    items: [
      { key: 'dashboard', label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    ]
  },
  {
    group: 'foundation',
    title: 'Career Foundation',
    items: [
      { key: 'assessment', label: 'Discovery Assessment', href: '/assessment', icon: Compass, step: '1' },
      { key: 'resume', label: 'Resume & ATS', href: '/resume', icon: FileText, step: '2' },
      { key: 'skills', label: 'Skill Matrix', href: '/skills', icon: Award, step: '3' },
      { key: 'roadmap', label: 'Roadmap & Tasks', href: '/roadmap', icon: MapPin, step: '4' },
    ]
  },
  {
    group: 'prep',
    title: 'Skill & Prep',
    items: [
      { key: 'practice', label: 'Micro Practice', href: '/practice', icon: Dumbbell, step: '5' },
      { key: 'interview', label: 'Mock Interview', href: '/interview', icon: Mic, step: '6' },
    ]
  },
  {
    group: 'opportunities',
    title: 'Opportunities',
    items: [
      { key: 'jobs', label: 'Job Engine', href: '/jobs', icon: Briefcase, step: '7' },
    ]
  },
  {
    group: 'readiness',
    title: 'Readiness & Profile',
    items: [
      { key: 'progress', label: 'Progress & Readiness', href: '/progress', icon: TrendingUp, step: '8' },
      { key: 'profile', label: 'Digital Twin Profile', href: '/profile', icon: Sparkles },
      { key: 'placement', label: 'Placement Readiness', href: '/placement', icon: GraduationCap },
    ]
  },
  {
    group: 'support',
    title: 'Support & Settings',
    items: [
      { key: 'chat', label: 'AI Career Assistant', href: '/chat', icon: MessageSquare },
      { key: 'guide', label: 'Help / Guide', href: '/guide', icon: BookOpen },
      { key: 'settings', label: 'Settings', href: '/settings', icon: Settings },
    ]
  }
];

interface SidebarProps {
  isMobileOpen?: boolean;
  onClose?: () => void;
}

export default function Sidebar({ isMobileOpen = false, onClose }: SidebarProps) {
  const pathname = usePathname();
  const { user, logout, hasCompletedAssessment } = useAuth();
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

  const visibleGroups = !hasCompletedAssessment
    ? [
        {
          group: 'foundation',
          title: 'Mandatory First Step',
          items: [
            { key: 'assessment', label: 'Discovery Assessment', href: '/assessment', icon: Compass, step: '1' },
          ],
        },
      ]
    : NAV_GROUPS;

  const renderNavLinks = () => (
    <nav className="flex-1 overflow-y-auto px-3.5 py-4 space-y-5">
      {visibleGroups.map((grp) => (
        <div key={grp.group} className="space-y-1">
          {grp.title && (
            <div className="px-3 pt-1 pb-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-500">
              {grp.title}
            </div>
          )}
          <div className="space-y-1">
            {grp.items.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href || (item.href !== '/dashboard' && pathname.startsWith(`${item.href}/`));
              const itemLabel = t(`nav.${item.key}`, item.label);
              const isDiscovery = item.key === 'assessment';
              const showPulse = isDiscovery && !hasCompletedAssessment;

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => {
                    if (onClose) onClose();
                  }}
                  className={`group flex items-center justify-between px-3 py-2 rounded-xl text-xs sm:text-sm font-medium transition-all duration-200 ${
                    isActive
                      ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/40 shadow-sm shadow-indigo-500/10'
                      : showPulse
                      ? 'bg-amber-500/10 text-amber-300 border border-amber-500/30 hover:bg-amber-500/20'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
                  }`}
                >
                  <div className="flex items-center space-x-2.5 truncate">
                    <Icon className={`w-4 h-4 shrink-0 transition-colors ${
                      isActive ? 'text-indigo-400' : showPulse ? 'text-amber-400 animate-pulse' : 'text-slate-400 group-hover:text-slate-300'
                    }`} />
                    <span className="truncate">{itemLabel}</span>
                  </div>

                  {showPulse ? (
                    <span className="text-[10px] font-bold uppercase px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-400 border border-amber-500/30 animate-pulse">
                      Step 1
                    </span>
                  ) : item.step && (
                    <span className="text-[10px] text-slate-600 font-semibold opacity-0 group-hover:opacity-100 transition-opacity">
                      {item.step}
                    </span>
                  )}
                </Link>
              );
            })}
          </div>
        </div>
      ))}

      {!hasCompletedAssessment && (
        <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs space-y-1.5">
          <div className="flex items-center space-x-1.5 font-bold">
            <Lock className="w-3.5 h-3.5 text-amber-400" />
            <span>Features Locked</span>
          </div>
          <p className="text-[11px] text-slate-400 leading-snug">
            Complete your Discovery Assessment to unlock your Dashboard, Resume ATS, Skill Matrix, Roadmap, and other features.
          </p>
        </div>
      )}
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
          {hasCompletedAssessment && (
            <Link
              href="/settings"
              onClick={() => { if (onClose) onClose(); }}
              title={t('nav.settings', 'Settings')}
              className="p-1.5 rounded-lg text-slate-400 hover:text-indigo-400 hover:bg-indigo-500/10 transition"
            >
              <Settings className="w-4 h-4" />
            </Link>
          )}
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
