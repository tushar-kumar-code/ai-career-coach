'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';

export type ThemePreset = 'midnight' | 'cyberpunk' | 'ocean' | 'sunset' | 'emerald' | 'light';
export type AccentColor = 'indigo' | 'emerald' | 'violet' | 'rose' | 'amber' | 'cyan';

export interface ThemeSettings {
  theme: ThemePreset;
  accent: AccentColor;
  compactMode: boolean;
  animations: boolean;
  glowEffects: boolean;
}

const DEFAULT_SETTINGS: ThemeSettings = {
  theme: 'midnight',
  accent: 'indigo',
  compactMode: false,
  animations: true,
  glowEffects: true,
};

interface ThemeContextType extends ThemeSettings {
  setTheme: (theme: ThemePreset) => void;
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
        setSettings({
          ...DEFAULT_SETTINGS,
          ...parsed,
        });
      }
    } catch (err) {
      console.error('Failed to load theme settings from storage:', err);
    }
    setMounted(true);
  }, []);

  // Apply theme classes and attributes to document root whenever settings change
  useEffect(() => {
    if (!mounted || typeof document === 'undefined') return;

    const root = document.documentElement;

    // 1. Remove all existing theme and accent classes
    const themeClasses = ['theme-midnight', 'theme-cyberpunk', 'theme-ocean', 'theme-sunset', 'theme-emerald', 'theme-light'];
    const accentClasses = ['accent-indigo', 'accent-emerald', 'accent-violet', 'accent-rose', 'accent-amber', 'accent-cyan'];
    
    themeClasses.forEach((cls) => root.classList.remove(cls));
    accentClasses.forEach((cls) => root.classList.remove(cls));

    // 2. Add active theme & accent class
    root.classList.add(`theme-${settings.theme}`);
    root.classList.add(`accent-${settings.accent}`);

    // 3. Handle dark / light root class
    if (settings.theme === 'light') {
      root.classList.remove('dark');
      root.classList.add('light');
    } else {
      root.classList.remove('light');
      root.classList.add('dark');
    }

    // 4. Handle compact mode
    if (settings.compactMode) {
      root.classList.add('compact-ui');
    } else {
      root.classList.remove('compact-ui');
    }

    // 5. Handle animations
    if (!settings.animations) {
      root.classList.add('no-animations');
    } else {
      root.classList.remove('no-animations');
    }

    // 6. Handle glow effects
    if (settings.glowEffects) {
      root.classList.add('enable-glow');
    } else {
      root.classList.remove('enable-glow');
    }

    // Save to localStorage
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
    } catch (err) {
      console.error('Failed to save theme settings to storage:', err);
    }
  }, [settings, mounted]);

  const setTheme = (theme: ThemePreset) => {
    setSettings((prev) => ({ ...prev, theme }));
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
