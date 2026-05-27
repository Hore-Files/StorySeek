/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#3c6842',
        'on-primary': '#ffffff',
        'primary-container': '#a5d6a7',
        'on-primary-container': '#325e39',
        background: '#f9f9f9',
        'on-background': '#1a1c1c',
        surface: '#FFFFFF',
        'surface-dim': '#dadada',
        'surface-bright': '#f9f9f9',
        'on-surface': '#1a1c1c',
        'on-surface-variant': '#414940',
        'text-secondary': '#718096',
        'border-light': '#EDF2F7',
        'accent-sage-deep': '#96C289',
        'glass-overlay': 'rgba(255, 255, 255, 0.7)'
      },
      fontFamily: {
        heading: ['"Plus Jakarta Sans"', 'sans-serif'],
        body: ['Inter', 'sans-serif'],
      },
      borderRadius: {
        '2xl': '1.5rem',
      }
    },
  },
  plugins: [],
}
