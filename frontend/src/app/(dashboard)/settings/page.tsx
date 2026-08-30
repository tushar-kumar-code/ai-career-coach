'use client';

import { useState, useEffect } from 'react';
import {
  Settings,
  Key,
  User,
  Bell,
  Shield,
  Palette,
  Monitor,
  Zap,
  Sparkles,
  Eye,
  EyeOff,
  CheckCircle2,
  AlertCircle,
  Loader2,
  ExternalLink,
  Trash2,
  RefreshCw,
  Save,
  LogOut,
  Moon,
  Sun,
  Globe,
  Info,
  Layers,
} from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { useTheme } from '@/context/ThemeContext';
import {
  getSavedAIConfig,
  saveAIConfig,
  clearSavedAIConfig,
  testApiKey,
} from '@/lib/api-client';

type SettingsTab = 'ai' | 'account' | 'notifications' | 'appearance' | 'about';

export default function SettingsPage() {
  const { user, logout } = useAuth();
  const {
    theme,
    accent,
    compactMode,
    animations,
    glowEffects,
    setTheme,
    setAccent,
    setCompactMode,
    setAnimations,
    setGlowEffects,
    resetTheme,
  } = useTheme();
  const [activeTab, setActiveTab] = useState<SettingsTab>('ai');

  // --- AI Key State ---
  const [provider, setProvider] = useState<'groq' | 'gemini'>('groq');
  const [apiKey, setApiKey] = useState('');
  const [model, setModel] = useState('');
  const [showKey, setShowKey] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [keyResult, setKeyResult] = useState<{ success: boolean; message: string } | null>(null);
  const [hasKey, setHasKey] = useState(false);

  // --- Notification Prefs ---
  const [notifWeeklyReport, setNotifWeeklyReport] = useState(true);
  const [notifInterviewReminder, setNotifInterviewReminder] = useState(true);
  const [notifRoadmapProgress, setNotifRoadmapProgress] = useState(false);
  const [notifSaved, setNotifSaved] = useState(false);

  useEffect(() => {
    const cfg = getSavedAIConfig();
    setProvider((cfg.provider as 'groq' | 'gemini') || 'groq');
    setApiKey(cfg.apiKey || '');
    setModel(cfg.model || '');
    setHasKey(!!cfg.apiKey);

    const notifPrefs = JSON.parse(localStorage.getItem('notif_prefs') || '{}');
    setNotifWeeklyReport(notifPrefs.weeklyReport ?? true);
    setNotifInterviewReminder(notifPrefs.interviewReminder ?? true);
    setNotifRoadmapProgress(notifPrefs.roadmapProgress ?? false);
  }, []);

  const handleTestKey = async () => {
    if (!apiKey.trim()) {
      setKeyResult({ success: false, message: 'Please enter an API key to test.' });
      return;
    }
    setIsTesting(true);
    setKeyResult(null);
    try {
      const res = await testApiKey(provider, apiKey.trim(), model || undefined);
      setKeyResult({ success: true, message: res.message || 'Key verified successfully!' });
    } catch (err: any) {
      setKeyResult({ success: false, message: err.message || 'Key verification failed.' });
    } finally {
      setIsTesting(false);
    }
  };

  const handleSaveKey = () => {
    if (!apiKey.trim()) {
      setKeyResult({ success: false, message: 'API Key cannot be empty.' });
      return;
    }
    setIsSaving(true);
    saveAIConfig(provider, apiKey.trim(), model || undefined);
    setHasKey(true);
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new Event('ai-config-updated'));
    }
    setTimeout(() => {
      setIsSaving(false);
      setKeyResult({ success: true, message: 'API Key saved and activated for all AI features!' });
    }, 400);
  };

  const handleClearKey = () => {
    clearSavedAIConfig();
    setApiKey('');
    setModel('');
    setHasKey(false);
    setKeyResult(null);
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new Event('ai-config-updated'));
    }
  };

  const handleSaveNotifications = () => {
    localStorage.setItem('notif_prefs', JSON.stringify({
      weeklyReport: notifWeeklyReport,
      interviewReminder: notifInterviewReminder,
      roadmapProgress: notifRoadmapProgress,
    }));
    setNotifSaved(true);
    setTimeout(() => setNotifSaved(false), 2000);
  };

  const TABS: { id: SettingsTab; label: string; icon: React.ElementType }[] = [
    { id: 'ai', label: 'AI & API Key', icon: Key },
    { id: 'account', label: 'Account', icon: User },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'appearance', label: 'Appearance', icon: Palette },
    { id: 'about', label: 'About', icon: Info },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Page Header */}
      <div className="flex items-center space-x-3">
        <div className="w-10 h-10 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300">
          <Settings className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-xl font-extrabold text-white">Settings</h1>
          <p className="text-xs text-slate-400">Manage your AI configuration, account, and preferences</p>
        </div>
      </div>

      <div className="flex flex-col lg:flex-row gap-6">
        {/* Sidebar Tabs */}
        <div className="lg:w-52 shrink-0">
          <nav className="space-y-1 bg-slate-900/60 rounded-2xl border border-slate-800 p-2">
            {TABS.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                  activeTab === id
                    ? 'bg-indigo-600/20 text-indigo-400 border border-indigo-500/30'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                }`}
              >
                <Icon className={`w-4 h-4 ${activeTab === id ? 'text-indigo-400' : 'text-slate-500'}`} />
                <span>{label}</span>
              </button>
            ))}
          </nav>
        </div>

        {/* Content Panel */}
        <div className="flex-1 min-w-0">

          {/* ─── AI & API KEY TAB ─── */}
          {activeTab === 'ai' && (
            <div className="space-y-5">
              <div className="p-5 sm:p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-5">
                <div>
                  <h2 className="text-base font-bold text-white mb-0.5">AI Engine Configuration</h2>
                  <p className="text-xs text-slate-400">
                    Select your AI provider and manage your API key. Used for Career Coach Chat, Mock Interviews, Resume Analysis, and Roadmap Generation.
                  </p>
                </div>

                {/* Current Status */}
                <div className={`p-3.5 rounded-xl border flex items-center gap-3 ${
                  hasKey
                    ? 'bg-emerald-500/10 border-emerald-500/30'
                    : 'bg-amber-500/10 border-amber-500/30'
                }`}>
                  {hasKey
                    ? <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    : <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />}
                  <div>
                    <p className={`text-xs font-semibold ${hasKey ? 'text-emerald-300' : 'text-amber-300'}`}>
                      {hasKey ? `AI Active — Provider: ${provider.toUpperCase()}` : 'No API Key configured'}
                    </p>
                    <p className="text-[11px] text-slate-400 mt-0.5">
                      {hasKey ? 'All AI features are unlocked and ready to use.' : 'Configure a key below to unlock AI features.'}
                    </p>
                  </div>
                </div>

                {/* Provider Select */}
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-2">AI Provider</label>
                  <div className="grid grid-cols-2 gap-3">
                    {([
                      { id: 'groq', label: 'Groq', sub: 'Llama 3.3 70B · Fast & Free', icon: Zap, iconColor: 'text-amber-400', badge: 'Recommended', badgeColor: 'bg-indigo-500/20 text-indigo-300' },
                      { id: 'gemini', label: 'Google Gemini', sub: 'Gemini 2.5 Flash · Free tier', icon: Sparkles, iconColor: 'text-sky-400', badge: 'Google AI', badgeColor: 'bg-sky-500/20 text-sky-300' },
                    ] as const).map(({ id, label, sub, icon: Icon, iconColor, badge, badgeColor }) => (
                      <button
                        key={id}
                        type="button"
                        onClick={() => { setProvider(id); setKeyResult(null); }}
                        className={`p-3.5 rounded-xl border flex flex-col text-left transition ${
                          provider === id
                            ? 'bg-indigo-600/15 border-indigo-500 ring-1 ring-indigo-500'
                            : 'bg-slate-950/40 border-slate-800 hover:border-slate-700'
                        }`}
                      >
                        <div className="flex items-center justify-between w-full mb-1">
                          <span className={`font-bold text-sm text-slate-200 flex items-center gap-1.5`}>
                            <Icon className={`w-3.5 h-3.5 ${iconColor}`} /> {label}
                          </span>
                          <span className={`text-[10px] px-1.5 py-0.5 rounded font-semibold ${badgeColor}`}>{badge}</span>
                        </div>
                        <span className="text-xs text-slate-500">{sub}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* API Key Input */}
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="text-xs font-semibold text-slate-300">API Key</label>
                    <a
                      href={provider === 'groq' ? 'https://console.groq.com/keys' : 'https://aistudio.google.com/app/apikey'}
                      target="_blank" rel="noreferrer"
                      className="text-xs text-indigo-400 hover:underline flex items-center gap-1"
                    >
                      Get free key <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                  <div className="relative">
                    <input
                      type={showKey ? 'text' : 'password'}
                      value={apiKey}
                      onChange={(e) => { setApiKey(e.target.value); setKeyResult(null); }}
                      placeholder={provider === 'groq' ? 'gsk_...' : 'AIzaSy...'}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 pr-10 font-mono"
                    />
                    <button
                      type="button"
                      onClick={() => setShowKey(!showKey)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200"
                    >
                      {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>

                  {/* Optional Model Override */}
                  <div className="mt-2">
                    <input
                      type="text"
                      value={model}
                      onChange={(e) => setModel(e.target.value)}
                      placeholder="Model override (optional, e.g. llama-3.3-70b-versatile)"
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-slate-300 placeholder-slate-600 focus:outline-none focus:ring-1 focus:ring-indigo-500/50 font-mono"
                    />
                  </div>

                  <p className="text-[11px] text-slate-500 mt-1.5 flex items-center gap-1">
                    <Shield className="w-3 h-3 text-emerald-400" />
                    Saved in browser localStorage — never sent to our servers.
                  </p>
                </div>

                {/* Key test result */}
                {keyResult && (
                  <div className={`p-3.5 rounded-xl border text-xs flex items-start gap-2.5 ${
                    keyResult.success
                      ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                      : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
                  }`}>
                    {keyResult.success
                      ? <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                      : <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />}
                    <span>{keyResult.message}</span>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex items-center justify-between pt-1">
                  {hasKey && (
                    <button
                      type="button"
                      onClick={handleClearKey}
                      className="text-xs text-rose-400 hover:text-rose-300 flex items-center gap-1.5 px-3 py-1.5 rounded-lg hover:bg-rose-500/10 transition"
                    >
                      <Trash2 className="w-3.5 h-3.5" /> Remove Key
                    </button>
                  )}
                  <div className="flex items-center gap-2 ml-auto">
                    <button
                      type="button"
                      onClick={handleTestKey}
                      disabled={isTesting || !apiKey.trim()}
                      className="px-3.5 py-2 text-xs font-semibold rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 transition flex items-center gap-1.5 disabled:opacity-50"
                    >
                      {isTesting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
                      {isTesting ? 'Testing...' : 'Test Key'}
                    </button>
                    <button
                      type="button"
                      onClick={handleSaveKey}
                      disabled={isSaving || !apiKey.trim()}
                      className="px-4 py-2 text-xs font-bold rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white transition flex items-center gap-1.5 disabled:opacity-50 shadow-md shadow-indigo-600/20"
                    >
                      {isSaving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
                      {isSaving ? 'Saving...' : 'Save & Activate'}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ─── ACCOUNT TAB ─── */}
          {activeTab === 'account' && (
            <div className="space-y-5">
              <div className="p-5 sm:p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-5">
                <div>
                  <h2 className="text-base font-bold text-white mb-0.5">Account Details</h2>
                  <p className="text-xs text-slate-400">Your profile and authentication information.</p>
                </div>

                <div className="flex items-center space-x-4 p-4 bg-slate-950/60 rounded-xl border border-slate-800">
                  <div className="w-14 h-14 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center text-lg font-extrabold text-white shrink-0">
                    {user?.full_name
                      ? user.full_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
                      : user?.email?.[0]?.toUpperCase() || 'U'}
                  </div>
                  <div className="overflow-hidden">
                    <p className="font-bold text-white text-sm">{user?.full_name || 'Candidate'}</p>
                    <p className="text-xs text-slate-400 truncate">{user?.email}</p>
                    <span className="inline-flex mt-1 px-2 py-0.5 text-[10px] font-semibold bg-indigo-500/15 text-indigo-300 border border-indigo-500/20 rounded-full">
                      {user?.is_superuser ? 'Admin Account' : 'Candidate Account'}
                    </span>
                  </div>
                </div>

                <div className="space-y-3 text-sm">
                  <div className="flex justify-between items-center py-2.5 border-b border-slate-800">
                    <span className="text-slate-400 text-xs">Full Name</span>
                    <span className="text-slate-200 text-xs font-medium">{user?.full_name || '—'}</span>
                  </div>
                  <div className="flex justify-between items-center py-2.5 border-b border-slate-800">
                    <span className="text-slate-400 text-xs">Email Address</span>
                    <span className="text-slate-200 text-xs font-medium">{user?.email || '—'}</span>
                  </div>
                  <div className="flex justify-between items-center py-2.5 border-b border-slate-800">
                    <span className="text-slate-400 text-xs">Account Status</span>
                    <span className="text-emerald-400 text-xs font-medium">Active</span>
                  </div>
                  <div className="flex justify-between items-center py-2.5">
                    <span className="text-slate-400 text-xs">Authentication</span>
                    <span className="text-slate-200 text-xs font-medium">JWT / Local Auth</span>
                  </div>
                </div>

                <div className="pt-2 border-t border-slate-800">
                  <button
                    onClick={logout}
                    className="flex items-center gap-2 px-4 py-2 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 text-rose-400 text-xs font-semibold transition"
                  >
                    <LogOut className="w-3.5 h-3.5" />
                    Sign Out of Account
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* ─── NOTIFICATIONS TAB ─── */}
          {activeTab === 'notifications' && (
            <div className="p-5 sm:p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-5">
              <div>
                <h2 className="text-base font-bold text-white mb-0.5">Notification Preferences</h2>
                <p className="text-xs text-slate-400">Control which activity notifications and reminders you receive.</p>
              </div>

              <div className="space-y-4">
                {[
                  { label: 'Weekly Progress Report', sub: 'Receive a summary of your career progress every week', value: notifWeeklyReport, setter: setNotifWeeklyReport },
                  { label: 'Interview Practice Reminders', sub: 'Get reminded to practice mock interviews regularly', value: notifInterviewReminder, setter: setNotifInterviewReminder },
                  { label: 'Roadmap Milestone Alerts', sub: 'Notify me when I reach a roadmap milestone', value: notifRoadmapProgress, setter: setNotifRoadmapProgress },
                ].map(({ label, sub, value, setter }) => (
                  <div key={label} className="flex items-center justify-between py-3 border-b border-slate-800 last:border-0">
                    <div>
                      <p className="text-sm text-white font-medium">{label}</p>
                      <p className="text-xs text-slate-500 mt-0.5">{sub}</p>
                    </div>
                    <button
                      type="button"
                      onClick={() => setter(!value)}
                      className={`relative w-10 h-5 rounded-full transition-colors ${value ? 'bg-indigo-600' : 'bg-slate-700'}`}
                    >
                      <span className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform ${value ? 'translate-x-5' : 'translate-x-0'}`} />
                    </button>
                  </div>
                ))}
              </div>

              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={handleSaveNotifications}
                  className="px-4 py-2 text-xs font-bold rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white transition flex items-center gap-1.5 shadow-md"
                >
                  <Save className="w-3.5 h-3.5" />
                  Save Preferences
                </button>
                {notifSaved && (
                  <span className="text-xs text-emerald-400 flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Saved!
                  </span>
                )}
              </div>
            </div>
          )}

          {/* ─── APPEARANCE TAB ─── */}
          {activeTab === 'appearance' && (
            <div className="p-5 sm:p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-base font-bold text-white mb-0.5">Appearance & Theme Studio</h2>
                  <p className="text-xs text-slate-400">Customize the platform theme, ambient glow, and color palette in real-time.</p>
                </div>
                <button
                  type="button"
                  onClick={resetTheme}
                  className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-950/60 border border-slate-800 hover:border-slate-700 transition"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  Reset Defaults
                </button>
              </div>

              {/* Theme Presets Grid */}
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2.5">
                  Theme Presets (Instant Live Switch)
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {[
                    { id: 'midnight' as const, name: 'Midnight Obsidian', desc: 'Deep slate with radiant indigo and purple aura', icon: Moon, bg: 'bg-slate-950', accent: 'from-indigo-500 to-purple-500' },
                    { id: 'cyberpunk' as const, name: 'Cyber Neon', desc: 'Deep void black with vibrant neon violet & fuchsia glow', icon: Sparkles, bg: 'bg-[#07070d]', accent: 'from-purple-500 to-pink-500' },
                    { id: 'ocean' as const, name: 'Ocean Deep', desc: 'Deep oceanic teal with electric cyan & emerald shine', icon: Layers, bg: 'bg-[#040e1a]', accent: 'from-cyan-500 to-blue-500' },
                    { id: 'sunset' as const, name: 'Sunset Amber', desc: 'Rich espresso with warm golden amber & rose accents', icon: Zap, bg: 'bg-[#100b09]', accent: 'from-amber-500 to-orange-500' },
                    { id: 'emerald' as const, name: 'Emerald Forest', desc: 'High-tech dark forest with mint green highlights', icon: Sparkles, bg: 'bg-[#041209]', accent: 'from-emerald-500 to-teal-500' },
                    { id: 'light' as const, name: 'Crisp Modern Light', desc: 'Clean, high-contrast professional daytime mode', icon: Sun, bg: 'bg-slate-100', accent: 'from-indigo-600 to-blue-600' },
                  ].map((t) => {
                    const Icon = t.icon;
                    const isSelected = theme === t.id;
                    return (
                      <button
                        key={t.id}
                        type="button"
                        onClick={() => setTheme(t.id)}
                        className={`p-3.5 rounded-2xl border text-left transition-all relative flex flex-col justify-between group ${
                          isSelected
                            ? 'bg-slate-800/90 border-indigo-500 ring-2 ring-indigo-500/80 shadow-lg shadow-indigo-500/10'
                            : 'bg-slate-950/60 border-slate-800/90 hover:border-slate-700'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2 w-full">
                          <div className="flex items-center space-x-2.5">
                            <div className={`w-7 h-7 rounded-xl ${t.bg} border border-slate-700/80 flex items-center justify-center shadow-inner`}>
                              <div className={`w-3 h-3 rounded-full bg-gradient-to-tr ${t.accent}`} />
                            </div>
                            <span className="font-bold text-xs text-white">{t.name}</span>
                          </div>
                          {isSelected && (
                            <span className="w-4 h-4 rounded-full bg-indigo-500 text-white flex items-center justify-center shadow-sm">
                              <CheckCircle2 className="w-3 h-3" />
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] text-slate-400 leading-snug">{t.desc}</p>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Accent Color Palette */}
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2.5">
                  Accent Color Highlight
                </label>
                <div className="grid grid-cols-3 sm:grid-cols-6 gap-2.5">
                  {[
                    { id: 'indigo' as const, name: 'Indigo', color: 'bg-indigo-500' },
                    { id: 'emerald' as const, name: 'Emerald', color: 'bg-emerald-500' },
                    { id: 'violet' as const, name: 'Violet', color: 'bg-purple-500' },
                    { id: 'rose' as const, name: 'Rose', color: 'bg-rose-500' },
                    { id: 'amber' as const, name: 'Amber', color: 'bg-amber-500' },
                    { id: 'cyan' as const, name: 'Cyan', color: 'bg-cyan-500' },
                  ].map((a) => {
                    const isSelected = accent === a.id;
                    return (
                      <button
                        key={a.id}
                        type="button"
                        onClick={() => setAccent(a.id)}
                        className={`p-2.5 rounded-xl border flex flex-col items-center gap-1.5 transition ${
                          isSelected
                            ? 'bg-slate-800 border-indigo-500 ring-1 ring-indigo-500 shadow-md'
                            : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
                        }`}
                      >
                        <span className={`w-6 h-6 rounded-full ${a.color} shadow-sm`} />
                        <span className="text-[11px] font-semibold text-slate-200">{a.name}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Display & Layout Options */}
              <div className="space-y-4 pt-3 border-t border-slate-800/80">
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-400">
                  Layout & Visual Effects
                </label>
                {[
                  { label: 'Compact Density', sub: 'Reduce padding and spacing for more content visibility', value: compactMode, setter: setCompactMode },
                  { label: 'Smooth Micro-Animations', sub: 'Enable transitions and interactive effects across pages', value: animations, setter: setAnimations },
                  { label: 'Ambient Glow & Gradient Borders', sub: 'Add soft glowing highlights around active cards and elements', value: glowEffects, setter: setGlowEffects },
                ].map(({ label, sub, value, setter }) => (
                  <div key={label} className="flex items-center justify-between py-3 border-b border-slate-800/60 last:border-0">
                    <div>
                      <p className="text-sm text-white font-medium">{label}</p>
                      <p className="text-xs text-slate-500 mt-0.5">{sub}</p>
                    </div>
                    <button
                      type="button"
                      onClick={() => setter(!value)}
                      className={`relative w-10 h-5 rounded-full transition-colors ${value ? 'bg-indigo-600' : 'bg-slate-700'}`}
                    >
                      <span className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform ${value ? 'translate-x-5' : 'translate-x-0'}`} />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ─── ABOUT TAB ─── */}
          {activeTab === 'about' && (
            <div className="p-5 sm:p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-5">
              <div>
                <h2 className="text-base font-bold text-white mb-0.5">About AI Career Coach</h2>
                <p className="text-xs text-slate-400">Platform information and technology stack.</p>
              </div>

              <div className="space-y-3 text-sm">
                {[
                  { label: 'Platform Version', value: '1.0.0' },
                  { label: 'Frontend Framework', value: 'Next.js 14 (App Router)' },
                  { label: 'Backend Framework', value: 'FastAPI + SQLAlchemy' },
                  { label: 'Database', value: 'SQLite (aiosqlite)' },
                  { label: 'AI Providers', value: 'Groq (Llama 3.3 70B) · Google Gemini 2.5 Flash' },
                  { label: 'Authentication', value: 'JWT (python-jose) + BCrypt' },
                  { label: 'License', value: 'MIT · Open Source' },
                ].map(({ label, value }) => (
                  <div key={label} className="flex justify-between items-center py-2.5 border-b border-slate-800 last:border-0">
                    <span className="text-slate-400 text-xs">{label}</span>
                    <span className="text-slate-200 text-xs font-medium">{value}</span>
                  </div>
                ))}
              </div>

              <div className="p-4 rounded-xl bg-gradient-to-br from-indigo-500/10 to-purple-500/10 border border-indigo-500/20 text-center">
                <Sparkles className="w-6 h-6 text-indigo-400 mx-auto mb-2" />
                <p className="text-xs text-slate-300 font-medium">AI Career Coach — Personal Career Intelligence Platform</p>
                <p className="text-[11px] text-slate-500 mt-1">Powered by LLMs · Built for students & early-career developers</p>
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
