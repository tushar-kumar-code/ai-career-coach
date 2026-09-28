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
            DEFAULT: '#17324D',
            hover: '#102A43',
            dark: '#0D1E2E',
            light: '#234668',
          },
          beige: {
            DEFAULT: '#B89B72',
            hover: '#A3845B',
            light: '#D9C19A',
            subtle: 'rgba(184, 155, 114, 0.12)',
            border: '#E7E2D8',
          },
          bg: '#FAF8F3',
          surface: '#FFFFFF',
          text: '#273444',
          muted: '#64748B',
          border: '#E7E2D8',
          success: '#2E7D5B',
          warning: '#C78A20',
          error: '#C75C5C',
          dark: {
            bg: '#0F172A',
            surface: '#172235',
            primary: '#D9C19A',
            accent: '#B89B72',
            text: '#F1F5F9',
            muted: '#A8B3C2',
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
