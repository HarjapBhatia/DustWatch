export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        critical: '#E24B4A',
        high: '#EF9F27',
        medium: '#378ADD',
        low: '#639922',
      },
      fontFamily: {
        sans: ['DM Sans', 'system-ui', 'sans-serif']
      }
    }
  },
  plugins: []
}
