module.exports = {
  content: [
    "./templates/**/*.html",
    "./static/**/*.js"
  ],
  theme: {
    extend: {
      colors: {
        primary: '#1e40af',
        secondary: '#1e293b',
        accent: '#3b82f6'
      }
    }
  },
  plugins: [
    require('@tailwindcss/forms')
  ]
} 