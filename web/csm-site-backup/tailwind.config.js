/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['CoFo Gothic', 'sans-serif'],
      },
      fontSize: {
        '8xl': '6rem',
      },
      transitionDuration: {
        '2000': '2000ms',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'orbit-horizontal': 'orbitHorizontal 30s linear infinite',
        'spin-slow': 'spin 8s linear infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(var(--tw-gradient-stops))',
      },
      keyframes: {
        glow: {
          '0%': { textShadow: '0 0 20px rgba(255,255,255,0.5)' },
          '100%': { textShadow: '0 0 30px rgba(255,255,255,0.8)' }
        }
      },
      dropShadow: {
        'glow': '0 0 10px rgba(255,255,255,0.35)',
      },
    },
  },
  plugins: [],
};