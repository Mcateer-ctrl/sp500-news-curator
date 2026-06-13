/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Geist', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['Geist Mono', 'ui-monospace', 'monospace'],
      },
      colors: {
        surface: {
          DEFAULT: '#fafaf9',
          alt: '#f5f5f4',
          hover: '#f0efed',
        },
        accent: {
          DEFAULT: '#2563eb',
          hover: '#1d4ed8',
          light: '#eff6ff',
        },
      },
      boxShadow: {
        'card': '0 1px 3px 0 rgba(0,0,0,0.04), 0 1px 2px -1px rgba(0,0,0,0.03)',
        'card-hover': '0 4px 12px -2px rgba(0,0,0,0.08), 0 2px 6px -2px rgba(0,0,0,0.04)',
        'pill': '0 2px 8px -2px rgba(0,0,0,0.08), 0 1px 3px -1px rgba(0,0,0,0.04)',
        'inner': 'inset 0 1px 1px rgba(255,255,255,0.5)',
      },
      borderRadius: {
        '2xl': '1rem',
        '3xl': '1.25rem',
        '4xl': '1.5rem',
        'pill': '9999px',
      },
      transitionTimingFunction: {
        'spring': 'cubic-bezier(0.32, 0.72, 0, 1)',
      },
    },
  },
  plugins: [],
}
