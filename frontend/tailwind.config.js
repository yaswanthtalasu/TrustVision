/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        trust: {
          50: '#F0F7FF',
          100: '#E0EFFE',
          500: '#0284C7',
          600: '#0369A1',
          900: '#0C4A6E',
        }
      }
    },
  },
  plugins: [],
}
