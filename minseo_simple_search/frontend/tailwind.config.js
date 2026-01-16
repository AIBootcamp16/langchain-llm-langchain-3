/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#27685d',
          50: '#f0f9f7',
          100: '#d9f0ec',
          200: '#b3e1d9',
          300: '#8dd2c6',
          400: '#67c3b3',
          500: '#27685d',
          600: '#1f534a',
          700: '#173e38',
          800: '#0f2925',
          900: '#071413',
        },
        'background-light': '#f9fafa',
        'background-dark': '#1c1f22',
        'text-muted': '#5e8781',
        'text-muted-light': '#9fb3af',
      },
      fontFamily: {
        display: ['Manrope', 'sans-serif'],
        sans: ['Manrope', 'Noto Sans KR', 'sans-serif'],
      },
      borderRadius: {
        DEFAULT: '0.25rem',
        lg: '0.5rem',
        xl: '0.75rem',
        '2xl': '1rem',
        full: '9999px',
      },
    },
  },
  plugins: [],
};

