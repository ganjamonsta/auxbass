/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Design System Colors
        'accent': 'var(--c-accent)',
        'accent-light': 'var(--c-accent-light)',
        'accent-dark': 'var(--c-accent-dark)',
        'secondary': 'var(--c-secondary)',
        
        // Surface colors
        'surface-0': 'var(--c-bg-0)',
        'surface-1': 'var(--c-bg-1)',
        'surface-2': 'var(--c-bg-2)',
        'surface-3': 'var(--c-bg-3)',
        'surface-4': 'var(--c-bg-4)',
        
        // Text colors
        'text-1': 'var(--c-text-1)',
        'text-2': 'var(--c-text-2)',
        'text-3': 'var(--c-text-3)',
        'text-4': 'var(--c-text-4)',
        
        // Telegram theme colors (legacy)
        'tg-bg': 'var(--tg-theme-bg-color, #ffffff)',
        'tg-text': 'var(--tg-theme-text-color, #000000)',
        'tg-hint': 'var(--tg-theme-hint-color, #999999)',
        'tg-link': 'var(--tg-theme-link-color, #2481cc)',
        'tg-button': 'var(--tg-theme-button-color, #2481cc)',
        'tg-button-text': 'var(--tg-theme-button-text-color, #ffffff)',
        'tg-secondary-bg': 'var(--tg-theme-secondary-bg-color, #f0f0f0)',
      },
      borderRadius: {
        'xs': 'var(--r-xs)',
        'sm': 'var(--r-sm)',
        'md': 'var(--r-md)',
        'lg': 'var(--r-lg)',
        'xl': 'var(--r-xl)',
      },
      spacing: {
        'sp-1': 'var(--sp-1)',
        'sp-2': 'var(--sp-2)',
        'sp-3': 'var(--sp-3)',
        'sp-4': 'var(--sp-4)',
        'sp-5': 'var(--sp-5)',
        'sp-6': 'var(--sp-6)',
        'sp-8': 'var(--sp-8)',
        'sp-10': 'var(--sp-10)',
        'sp-12': 'var(--sp-12)',
      },
      boxShadow: {
        'neu-raised-sm': '3px 3px 6px var(--sh-dark), -2px -2px 4px var(--sh-light)',
        'neu-raised': '5px 5px 10px var(--sh-dark), -3px -3px 6px var(--sh-light)',
        'neu-raised-lg': '8px 8px 16px var(--sh-dark), -4px -4px 8px var(--sh-light)',
        'neu-inset': 'inset 3px 3px 6px var(--sh-inset-dark), inset -2px -2px 4px var(--sh-inset-light)',
        'neu-glow': '0 0 12px var(--c-accent-glow)',
      },
      fontFamily: {
        sans: 'var(--font-sans)',
        mono: 'var(--font-mono)',
      },
    },
  },
  plugins: [],
}
