/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}", "./public/index.html"],
  theme: {
    extend: {
      colors: {
        prism: { black: '#1A1A1A', red: '#E50914', gray: '#333333', white: '#FFFFFF' },
        gray: {
          50: '#f8f9fa', 100: '#f1f3f4', 200: '#e8eaed', 300: '#dadce0', 400: '#bdc1c6',
          500: '#9aa0a6', 600: '#80868b', 700: '#5f6368', 800: '#3c4043', 900: '#202124'
        }
      },
      fontFamily: { sans: ['Inter', 'system-ui', 'sans-serif'] },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite'
      },
      keyframes: {
        fadeIn: { '0%': { opacity: '0' }, '100%': { opacity: '1' } },
        slideUp: { '0%': { transform: 'translateY(10px)', opacity: '0' }, '100%': { transform: 'translateY(0)', opacity: '1' } }
      },
      boxShadow: {
        'prism': '0 4px 6px -1px rgba(229, 9, 20, 0.1), 0 2px 4px -1px rgba(229, 9, 20, 0.06)',
        'prism-lg': '0 10px 15px -3px rgba(229, 9, 20, 0.1), 0 4px 6px -2px rgba(229, 9, 20, 0.05)'
      }
    }
  },
  plugins: []
}
