/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        mint: { DEFAULT: '#B8D9CE', dark: '#6FA98C', light: '#E3F1EB' },
        lav: { DEFAULT: '#DAD3EE', dark: '#9C8FD1', light: '#EFEBF9' },
        sand: { DEFAULT: '#EAE4D8', dark: '#B7A98A', light: '#F5F1E9' },
        rose: { DEFAULT: '#E9D6D3', dark: '#C98B80', light: '#F6EBE9' },
        cream: '#F6F1EA',
        surface: '#FFFFFF',
        ink: '#14161B',
        muted: '#8B93A6',
        border: '#EAE4D8',
      },
      fontFamily: {
        sans: ['"Poppins"', '"Segoe UI"', 'sans-serif'],
      },
      borderRadius: {
        xl2: '1.75rem',
      },
      boxShadow: {
        soft: '0 8px 24px -8px rgba(20, 22, 27, 0.12)',
      },
    },
  },
  plugins: [],
}
