'use client';

import React from 'react';
import { X, Check, Sparkles, Moon, Sun, Palette, Zap, Layers, RefreshCw } from 'lucide-react';
import { useTheme, ThemePreset, AccentColor } from '@/context/ThemeContext';

interface ThemeModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const THEME_OPTIONS: {
  id: ThemePreset;
  name: string;
  desc: string;
  icon: React.ElementType;
  bgPreview: string;
  accentPreview: string;
  borderColor: string;
}[] = [
  {
    id: 'midnight',
    name: 'Midnight Obsidian',
    desc: 'Deep slate with radiant indigo and purple aura',
    icon: Moon,
    bgPreview: 'bg-slate-950',
    accentPreview: 'from-indigo-500 to-purple-500',
    borderColor: 'border-indigo-500/40',
  },
  {
    id: 'cyberpunk',
    name: 'Cyber Neon',
    desc: 'Deep void black with vibrant neon violet & fuchsia',
    icon: Sparkles,
    bgPreview: 'bg-[#07070d]',
    accentPreview: 'from-purple-500 to-pink-500',
    borderColor: 'border-purple-500/40',
  },
  {
    id: 'ocean',
    name: 'Ocean Deep',
    desc: 'Deep oceanic teal with electric cyan & emerald glow',
    icon: Layers,
    bgPreview: 'bg-[#040e1a]',
    accentPreview: 'from-cyan-500 to-blue-500',
    borderColor: 'border-cyan-500/40',
  },
  {
    id: 'sunset',
    name: 'Sunset Amber',
    desc: 'Rich dark espresso with warm golden amber glow',
    icon: Zap,
    bgPreview: 'bg-[#100b09]',
    accentPreview: 'from-amber-500 to-orange-500',
    borderColor: 'border-amber-500/40',
  },
  {
    id: 'emerald',
    name: 'Emerald Forest',
    desc: 'High-tech dark forest with mint emerald accents',
    icon: Sparkles,
    bgPreview: 'bg-[#041209]',
    accentPreview: 'from-emerald-500 to-teal-500',
    borderColor: 'border-emerald-500/40',
  },
  {
    id: 'light',
    name: 'Crisp Modern Light',
    desc: 'Clean, high-contrast professional light mode',
    icon: Sun,
    bgPreview: 'bg-slate-100',
    accentPreview: 'from-indigo-600 to-blue-600',
    borderColor: 'border-slate-300',
  },
];

const ACCENT_OPTIONS: { id: AccentColor; name: string; colorClass: string }[] = [
  { id: 'indigo', name: 'Indigo', colorClass: 'bg-indigo-500' },
  { id: 'emerald', name: 'Emerald', colorClass: 'bg-emerald-500' },
  { id: 'violet', name: 'Violet', colorClass: 'bg-purple-500' },
  { id: 'rose', name: 'Rose', colorClass: 'bg-rose-500' },
  { id: 'amber', name: 'Amber', colorClass: 'bg-amber-500' },
  { id: 'cyan', name: 'Cyan', colorClass: 'bg-cyan-500' },
];

export default function ThemeModal({ isOpen, onClose }: ThemeModalProps) {
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

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-xl shadow-2xl overflow-hidden animate-in zoom-in-95">
        {/* Header */}
        <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
          <div className="flex items-center space-x-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center text-white shadow-md">
              <Palette className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white leading-tight">Theme & Appearance Studio</h2>
              <p className="text-xs text-slate-400">Personalize your cockpit theme and colors in real-time</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-5 space-y-5 max-h-[70vh] overflow-y-auto scrollbar-thin scrollbar-thumb-slate-700">
          {/* Theme Presets */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2.5">
              Theme Presets (Live Preview)
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {THEME_OPTIONS.map((item) => {
                const Icon = item.icon;
                const isSelected = theme === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => setTheme(item.id)}
                    type="button"
                    className={`p-3 rounded-xl border text-left transition-all relative flex flex-col justify-between ${
                      isSelected
                        ? `bg-slate-800/80 ${item.borderColor} ring-2 ring-indigo-500 shadow-md`
                        : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <div className={`w-6 h-6 rounded-lg ${item.bgPreview} border border-slate-700 flex items-center justify-center shadow-sm`}>
                          <div className={`w-2.5 h-2.5 rounded-full bg-gradient-to-tr ${item.accentPreview}`} />
                        </div>
                        <span className="font-bold text-xs text-slate-200">{item.name}</span>
                      </div>
                      {isSelected && (
                        <span className="w-4 h-4 rounded-full bg-indigo-500 text-white flex items-center justify-center">
                          <Check className="w-2.5 h-2.5 stroke-[3]" />
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] text-slate-400 leading-snug">{item.desc}</p>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Accent Color Picker */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
              Accent Highlight
            </label>
            <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
              {ACCENT_OPTIONS.map((opt) => {
                const isSelected = accent === opt.id;
                return (
                  <button
                    key={opt.id}
                    onClick={() => setAccent(opt.id)}
                    type="button"
                    className={`p-2 rounded-xl border flex flex-col items-center gap-1.5 transition ${
                      isSelected
                        ? 'bg-slate-800 border-indigo-500 ring-1 ring-indigo-500'
                        : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
                    }`}
                  >
                    <span className={`w-5 h-5 rounded-full ${opt.colorClass} shadow-sm`} />
                    <span className="text-[10px] font-medium text-slate-300">{opt.name}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Display & Layout Options */}
          <div className="pt-2 border-t border-slate-800/80 space-y-3">
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-400">
              Display & Layout
            </label>
            <div className="space-y-2.5">
              <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/60 border border-slate-800">
                <div>
                  <p className="text-xs font-semibold text-slate-200">Compact Density</p>
                  <p className="text-[10px] text-slate-400">Reduce spacing for higher data visibility</p>
                </div>
                <button
                  type="button"
                  onClick={() => setCompactMode(!compactMode)}
                  className={`relative w-9 h-5 rounded-full transition-colors ${
                    compactMode ? 'bg-indigo-600' : 'bg-slate-700'
                  }`}
                >
                  <span
                    className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform ${
                      compactMode ? 'translate-x-4' : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>

              <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/60 border border-slate-800">
                <div>
                  <p className="text-xs font-semibold text-slate-200">Smooth Micro-Animations</p>
                  <p className="text-[10px] text-slate-400">Enable transitions and interactive effects</p>
                </div>
                <button
                  type="button"
                  onClick={() => setAnimations(!animations)}
                  className={`relative w-9 h-5 rounded-full transition-colors ${
                    animations ? 'bg-indigo-600' : 'bg-slate-700'
                  }`}
                >
                  <span
                    className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform ${
                      animations ? 'translate-x-4' : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>

              <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/60 border border-slate-800">
                <div>
                  <p className="text-xs font-semibold text-slate-200">Glow & Ambient Effects</p>
                  <p className="text-[10px] text-slate-400">Soft neon glow around active cards and elements</p>
                </div>
                <button
                  type="button"
                  onClick={() => setGlowEffects(!glowEffects)}
                  className={`relative w-9 h-5 rounded-full transition-colors ${
                    glowEffects ? 'bg-indigo-600' : 'bg-slate-700'
                  }`}
                >
                  <span
                    className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform ${
                      glowEffects ? 'translate-x-4' : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/80 flex items-center justify-between">
          <button
            onClick={resetTheme}
            type="button"
            className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1 px-2.5 py-1.5 rounded-lg hover:bg-slate-800 transition"
          >
            <RefreshCw className="w-3 h-3" />
            Reset Default
          </button>
          <button
            onClick={onClose}
            type="button"
            className="px-4 py-2 text-xs font-bold rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white transition shadow-md shadow-indigo-600/30"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
