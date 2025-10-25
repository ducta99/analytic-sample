import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: '#0f172a',
        secondary: '#1e293b',
        accent: '#0ea5e9',
        success: '#10b981',
        warning: '#f59e0b',
        error: '#ef4444',
        dark: '#0f172a',
      },
    },
  },
  plugins: [],
}

export default config
