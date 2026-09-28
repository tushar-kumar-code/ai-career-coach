'use client';

import React from 'react';
import { X, Check, Moon, Sun, Monitor, RefreshCw } from 'lucide-react';
import { useTheme, ThemeMode } from '@/context/ThemeContext';

interface ThemeModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const THEME_OPTIONS: {
  id: ThemeMode;
  name: string;
  desc: string;
  icon: React.ElementType;
  bgPreview: string;
  surfacePreview: string;
  accentColor: string;
  badge: string;
}[] = [
  {
    id: 'light',
    name: 'Clean Light Mode',
    desc: 'Crisp #F8FAFC canvas, white surfaces, Deep Navy typography & Teal accents',
    icon: Sun,
    bgPreview: '#F8FAFC',
    surfacePreview: '#FFFFFF',
    accentColor: '#247B7B',
    badge: 'Recommended',
  },
  {
    id: 'dark',
    name: 'Executive Dark Mode',
    desc: 'Deep #0F172A slate canvas, #162235 navy surfaces & luminous Teal accents',
    icon: Moon,
    bgPreview: '#0F172A',
    surfacePreview: '#162235',
    accentColor: '#5FA8A8',
    badge: 'High Contrast',
  },
  {
    id: 'system',
    name: 'System Default',
    desc: 'Automatically matches your device operating system theme preference',
    icon: Monitor,
    bgPreview: '#17324D',
    surfacePreview: '#243447',
    accentColor: '#247B7B',
    badge: 'Adaptive',
  },
];

export default function ThemeModal({ isOpen, onClose }: ThemeModalProps) {
  const {
    mode,
    compactMode,
    animations,
    setMode,
    setCompactMode,
    setAnimations,
    resetTheme,
  } = useTheme();

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/60 backdrop-blur-sm animate-in fade-in">
      <div className="w-full max-w-lg bg-white dark:bg-[#162235] border border-slate-200 dark:border-[#293548] rounded-3xl shadow-2xl p-6 sm:p-7 space-y-6 text-[#243447] dark:text-[#E2E8F0]">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-[#293548]">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-2xl bg-[#17324D] dark:bg-[#1E2D44] border border-[#247B7B]/30 flex items-center justify-center text-[#247B7B] dark:text-[#5FA8A8]">
              <Sun className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-[#17324D] dark:text-white">Theme & Platform Appearance</h3>
              <p className="text-xs text-[#64748B] dark:text-[#94A3B8]">Unified Deep Navy & Teal Career Brand</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-[#1E2D44] transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Theme Mode Selector */}
        <div className="space-y-3">
          <label className="text-xs font-bold uppercase tracking-wider text-[#64748B] dark:text-[#94A3B8]">
            Color Theme Mode
          </label>
          <div className="grid grid-cols-1 gap-3">
            {THEME_OPTIONS.map((opt) => {
              const Icon = opt.icon;
              const isSelected = mode === opt.id;
              return (
                <button
                  key={opt.id}
                  type="button"
                  onClick={() => setMode(opt.id)}
                  className={`p-4 rounded-2xl border text-left transition-all flex items-center justify-between group ${
                    isSelected
                      ? 'border-[#247B7B] bg-[#247B7B]/10 dark:bg-[#247B7B]/20 ring-2 ring-[#247B7B]/50'
                      : 'border-slate-200 dark:border-[#293548] bg-slate-50 dark:bg-[#0F172A]/50 hover:border-slate-300 dark:hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center space-x-3.5">
                    <div
                      className="w-10 h-10 rounded-xl flex items-center justify-center border shadow-sm"
                      style={{
                        backgroundColor: opt.surfacePreview,
                        borderColor: isSelected ? opt.accentColor : '#E2E8F0',
                      }}
                    >
                      <Icon className="w-5 h-5" style={{ color: opt.accentColor }} />
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-bold text-sm text-[#17324D] dark:text-white">{opt.name}</span>
                        <span className="text-[10px] px-2 py-0.5 rounded-full font-semibold bg-[#247B7B]/10 text-[#247B7B] dark:text-[#5FA8A8]">
                          {opt.badge}
                        </span>
                      </div>
                      <p className="text-xs text-[#64748B] dark:text-[#94A3B8] mt-0.5">{opt.desc}</p>
                    </div>
                  </div>

                  <div className="ml-4 shrink-0">
                    <div
                      className={`w-6 h-6 rounded-full flex items-center justify-center border transition-all ${
                        isSelected
                          ? 'bg-[#247B7B] text-white border-[#247B7B]'
                          : 'border-slate-300 dark:border-slate-600'
                      }`}
                    >
                      {isSelected && <Check className="w-3.5 h-3.5" />}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Comfort Controls */}
        <div className="pt-2 border-t border-slate-100 dark:border-[#293548] space-y-3">
          <div className="flex items-center justify-between text-xs py-1">
            <div>
              <span className="font-semibold text-[#17324D] dark:text-white">Compact Interface Spacing</span>
              <p className="text-[#64748B] dark:text-[#94A3B8] text-[11px]">Reduces padding for dense workspace overview</p>
            </div>
            <button
              type="button"
              onClick={() => setCompactMode(!compactMode)}
              className={`relative w-10 h-5 rounded-full transition-colors ${
                compactMode ? 'bg-[#247B7B]' : 'bg-slate-300 dark:bg-slate-700'
              }`}
            >
              <span
                className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform ${
                  compactMode ? 'translate-x-5' : 'translate-x-0'
                }`}
              />
            </button>
          </div>

          <div className="flex items-center justify-between text-xs py-1">
            <div>
              <span className="font-semibold text-[#17324D] dark:text-white">Interface Transitions & Animations</span>
              <p className="text-[#64748B] dark:text-[#94A3B8] text-[11px]">Smooth transitions across panels and states</p>
            </div>
            <button
              type="button"
              onClick={() => setAnimations(!animations)}
              className={`relative w-10 h-5 rounded-full transition-colors ${
                animations ? 'bg-[#247B7B]' : 'bg-slate-300 dark:bg-slate-700'
              }`}
            >
              <span
                className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform ${
                  animations ? 'translate-x-5' : 'translate-x-0'
                }`}
              />
            </button>
          </div>
        </div>

        {/* Footer */}
        <div className="pt-3 border-t border-slate-100 dark:border-[#293548] flex items-center justify-between">
          <button
            type="button"
            onClick={resetTheme}
            className="text-xs text-[#64748B] dark:text-[#94A3B8] hover:text-[#17324D] dark:hover:text-white flex items-center gap-1.5 transition"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Reset Defaults
          </button>
          <button
            type="button"
            onClick={onClose}
            className="px-5 py-2 rounded-xl text-xs font-bold bg-[#17324D] dark:bg-[#247B7B] hover:bg-[#102A43] dark:hover:bg-[#1D6464] text-white transition shadow-sm"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
