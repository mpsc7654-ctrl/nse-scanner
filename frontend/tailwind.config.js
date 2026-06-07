/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        surface: { DEFAULT: '#0f1117', 2: '#161b27', 3: '#1e2535', border: '#2a3347' },
        green: { DEFAULT: '#00d084', muted: '#003d26' },
        red: { DEFAULT: '#ff4d4d', muted: '#3d0000' },
        amber: { DEFAULT: '#f59e0b', muted: '#3d2600' },
        blue: { DEFAULT: '#3b82f6', muted: '#0d1f3d' },
      },
      fontFamily: { mono: ['JetBrains Mono', 'monospace'] },
    },
  },
  plugins: [],
}
