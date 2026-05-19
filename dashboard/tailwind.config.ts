import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: "#08090b",
        surface: "#0f1014",
        "surface-2": "#15171c",
        border: "#1f2128",
        "border-strong": "#2a2d36",
        text: "#f4f4f6",
        muted: "#6b6e78",
        "muted-strong": "#9ca0ac",
        accent: "#00B4FC",
        "accent-soft": "#7dd3fc",
        urgent: "#00B4FC",
        high: "#00B4FC",
        medium: "#00B4FC",
        low: "#ffffff",
        done: "#ffffff",
        progress: "#00B4FC",
        // Camuflagem azul (aba Missões) — mantido por compat
        "camo-base": "#08090b",
        "camo-deep": "#050505",
        "camo-mid": "#101113",
        "camo-light": "#18191d",
        "camo-cyan": "#00B4FC",
        "camo-amber": "#ffffff",
        "camo-line": "#27292f",
        // Paleta Missões nova: preto / branco / azul elétrico
        "ms-bg": "#050505",
        "ms-card": "#101113",
        "ms-card-2": "#18191d",
        "ms-border": "#27292f",
        "ms-border-strong": "#3a3d45",
        "ms-text": "#ffffff",
        "ms-muted": "#777b84",
        "ms-muted-strong": "#b7bbc4",
        "ms-blue": "#00B4FC",
        "ms-blue-soft": "#7dd3fc",
        "ms-blue-deep": "#0284c7",
        // Monochrome mission palette with blue accents.
        "ms-green": "#ffffff",
        "ms-green-deep": "#0a0a0a",
        "ms-lilac": "#d8f3ff",
        "ms-lilac-deep": "#00B4FC",
        "ms-pink": "#d8f3ff",
        "ms-pink-deep": "#00B4FC",
        "ms-amber": "#f5f7fa",
        "ms-amber-deep": "#0a0a0a",
      },
      boxShadow: {
        card: "0 1px 0 0 rgba(255,255,255,0.04) inset, 0 1px 2px 0 rgba(0,0,0,0.4)",
        elevated: "0 10px 40px -10px rgba(0,0,0,0.6), 0 1px 0 0 rgba(255,255,255,0.04) inset",
        tactical: "0 8px 32px -12px rgba(34,211,238,0.25), 0 0 0 1px rgba(34,211,238,0.15) inset",
      },
      fontFamily: {
        sans: ['"Inter"', "-apple-system", "BlinkMacSystemFont", "Segoe UI", "sans-serif"],
        mono: ['"JetBrains Mono"', "ui-monospace", "monospace"],
        stencil: ['"Bebas Neue"', "Impact", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
