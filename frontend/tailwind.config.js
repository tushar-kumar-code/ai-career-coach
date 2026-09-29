/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        background: 'var(--background)',
        foreground: 'var(--foreground)',
        card: {
          DEFAULT: 'var(--card)',
          foreground: 'var(--card-foreground)',
        },
        primary: {
          DEFAULT: 'var(--primary)',
          foreground: 'var(--primary-foreground)',
        },
        secondary: {
          DEFAULT: 'var(--secondary)',
          foreground: 'var(--secondary-foreground)',
        },
        muted: {
          DEFAULT: 'var(--muted)',
          foreground: 'var(--muted-foreground)',
        },
        accent: {
          DEFAULT: 'var(--accent)',
          foreground: 'var(--accent-foreground)',
        },
        border: 'var(--border)',
        brand: {
          navy: {
            DEFAULT: '#0F172A',
            hover: '#1E293B',
            dark: '#020617',
            light: '#334155',
          },
          blue: {
            DEFAULT: '#2563EB',
            hover: '#1D4ED8',
            light: '#60A5FA',
            subtle: 'rgba(37, 99, 235, 0.10)',
            border: '#E2E8F0',
          },
          teal: {
            DEFAULT: '#0D9488',
            hover: '#0F766E',
            light: '#2DD4BF',
            subtle: 'rgba(13, 148, 136, 0.10)',
          },
          bg: '#F8FAFC',
          surface: '#FFFFFF',
          text: '#0F172A',
          muted: '#475569',
          border: '#E2E8F0',
          success: '#16A34A',
          warning: '#D97706',
          error: '#DC2626',
          dark: {
            bg: '#0F172A',
            surface: '#1E293B',
            primary: '#38BDF8',
            accent: '#2563EB',
            text: '#F8FAFC',
            muted: '#94A3B8',
            border: '#334155',
          },
        },
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
    },
  },
  plugins: [],
}
