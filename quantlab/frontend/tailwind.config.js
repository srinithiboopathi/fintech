/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        dark: {
          900: '#080c14',
          800: '#0e1626',
          700: '#142038',
          600: '#1f2e4d',
        },
        neon: {
          green: '#00f5a0',
          cyan: '#00d8ff',
          purple: '#9d4edd',
          rose: '#ff3366',
          amber: '#ffbe0b',
        }
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      }
    },
  },
  plugins: [],
}
