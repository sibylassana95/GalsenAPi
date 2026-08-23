/** @type {import('tailwindcss').Config} */
// Design system "Institutional Modern" — GalsenAPI 2.0
// Source : galsenapi_2.0_design/DESIGN.md
module.exports = {
  content: [
    './templates/**/*.html',
    './static/js/**/*.js',
  ],
  darkMode: ['class'],
  theme: {
    extend: {
      colors: {
        // Primaire — Vert forêt institutionnel
        'primary': '#003527',
        'on-primary': '#ffffff',
        'primary-container': '#064e3b',
        'on-primary-container': '#80bea6',
        'inverse-primary': '#95d3ba',
        // Secondaire — Or souverain (actions)
        'secondary': '#785a00',
        'on-secondary': '#ffffff',
        'secondary-container': '#fdc425',
        'on-secondary-container': '#6d5200',
        // Tertiaire / erreur
        'tertiary': '#640005',
        'on-tertiary': '#ffffff',
        'tertiary-container': '#8e000a',
        'on-tertiary-container': '#ff9488',
        'error': '#ba1a1a',
        'on-error': '#ffffff',
        'error-container': '#ffdad6',
        'on-error-container': '#93000a',
        // Surfaces & conteneurs
        'surface': '#fcfcfb',
        'surface-bright': '#f9f9ff',
        'surface-dim': '#cfdaf2',
        'container-lowest': '#ffffff',
        'container-low': '#f0f3ff',
        'container': '#e7eeff',
        'container-high': '#dee8ff',
        'container-highest': '#d8e3fb',
        'on-surface': '#111c2d',
        'on-surface-variant': '#404944',
        'inverse-surface': '#263143',
        'inverse-on-surface': '#ecf1ff',
        'surface-tint': '#2b6954',
        'surface-variant': '#d8e3fb',
        'background': '#f9f9ff',
        'on-background': '#111c2d',
        // Contours
        'outline': '#707974',
        'outline-variant': '#bfc9c3',
        // Variantes fixed
        'primary-fixed': '#b0f0d6',
        'primary-fixed-dim': '#95d3ba',
        'on-primary-fixed': '#002117',
        'on-primary-fixed-variant': '#0b513d',
        'secondary-fixed': '#ffdf9a',
        'secondary-fixed-dim': '#f7be1d',
        'on-secondary-fixed': '#251a00',
        'on-secondary-fixed-variant': '#5a4300',
        'tertiary-fixed': '#ffdad6',
        'tertiary-fixed-dim': '#ffb4ab',
        'on-tertiary-fixed': '#410002',
        'on-tertiary-fixed-variant': '#93000b',
        // Alias sémantiques
        'forest-deep': '#064e3b',
        'sovereign-gold': '#eab308',
        'alert-red': '#b91c1c',
        'border-subtle': '#e2e8f0',
      },
      fontFamily: {
        display: ['Montserrat', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        body: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
      borderRadius: {
        sm: '0.125rem',
        DEFAULT: '0.25rem',
        md: '0.375rem',
        lg: '0.5rem',
        xl: '0.75rem',
      },
      maxWidth: {
        container: '80rem',
      },
    },
  },
  plugins: [],
};
