'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';

export type ThemeMode = 'light' | 'dark' | 'system';
export type ThemePreset = ThemeMode | 'midnight' | 'cyberpunk' | 'ocean' | 'sunset' | 'emerald';
export type AccentColor = 'teal' | 'indigo' | 'emerald' | 'violet' | 'rose' | 'amber' | 'cyan';

export interface ThemeSettings {
  theme: ThemePreset;
  mode: ThemeMode;
  accent: AccentColor;
  compactMode: boolean;
  animations: boolean;
  glowEffects: boolean;
}

const DEFAULT_SETTINGS: ThemeSettings = {
  theme: 'light',
  mode: 'light',
  accent: 'teal',
  compactMode: false,
  animations: true,
  glowEffects: false,
};

interface ThemeContextType extends ThemeSettings {
  setTheme: (theme: ThemePreset) => void;
  setMode: (mode: ThemeMode) => void;
  setAccent: (accent: AccentColor) => void;
  setCompactMode: (compact: boolean) => void;
  setAnimations: (animations: boolean) => void;
  setGlowEffects: (glow: boolean) => void;
  resetTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

const STORAGE_KEY = 'ai_career_theme_settings';

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [settings, setSettings] = useState<ThemeSettings>(DEFAULT_SETTINGS);
  const [mounted, setMounted] = useState(false);

  // Load initial theme settings from localStorage
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        const resolvedTheme = parsed.theme || parsed.mode || 'light';
        const mode: ThemeMode = (resolvedTheme === 'dark' || resolvedTheme === 'midnight') ? 'dark' : (resolvedTheme === 'system' ? 'system' : 'light');
        setSettings({
          ...DEFAULT_SETTINGS,
          ...parsed,
          theme: mode,
          mode: mode,
        });
      }
    } catch (err) {
      console.error('Failed to load theme settings from storage:', err);
    }
    setMounted(true);
  }, []);

  // Synchronize theme mode with document.documentElement
  useEffect(() => {
    if (!mounted || typeof document === 'undefined') return;

    const root = document.documentElement;

    const applyTheme = (isDark: boolean) => {
      if (isDark) {
        root.classList.remove('light');
        root.classList.add('dark');
        root.setAttribute('data-theme', 'dark');
      } else {
        root.classList.remove('dark');
        root.classList.add('light');
        root.setAttribute('data-theme', 'light');
      }
    };

    if (settings.mode === 'system' || settings.theme === 'system') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      applyTheme(mediaQuery.matches);

      const handleChange = (e: MediaQueryListEvent) => {
        applyTheme(e.matches);
      };

      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    } else {
      const isDark = settings.mode === 'dark' || settings.theme === 'dark' || settings.theme === 'midnight';
      applyTheme(isDark);
    }

    // Save to localStorage
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
    } catch (err) {
      console.error('Failed to save theme settings to storage:', err);
    }
  }, [settings, mounted]);

  const setTheme = (theme: ThemePreset) => {
    const resolvedMode: ThemeMode = (theme === 'dark' || theme === 'midnight') ? 'dark' : (theme === 'system' ? 'system' : 'light');
    setSettings((prev) => ({ ...prev, theme: resolvedMode, mode: resolvedMode }));
  };

  const setMode = (mode: ThemeMode) => {
    setSettings((prev) => ({ ...prev, theme: mode, mode }));
  };

  const setAccent = (accent: AccentColor) => {
    setSettings((prev) => ({ ...prev, accent }));
  };

  const setCompactMode = (compactMode: boolean) => {
    setSettings((prev) => ({ ...prev, compactMode }));
  };

  const setAnimations = (animations: boolean) => {
    setSettings((prev) => ({ ...prev, animations }));
  };

  const setGlowEffects = (glowEffects: boolean) => {
    setSettings((prev) => ({ ...prev, glowEffects }));
  };

  const resetTheme = () => {
    setSettings(DEFAULT_SETTINGS);
  };

  return (
    <ThemeContext.Provider
      value={{
        ...settings,
        setTheme,
        setMode,
        setAccent,
        setCompactMode,
        setAnimations,
        setGlowEffects,
        resetTheme,
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
