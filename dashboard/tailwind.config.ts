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
        accent: "#ff5a1f",
        "accent-soft": "#ff7c4f",
        urgent: "#ef4444",
        high: "#f97316",
        medium: "#3b82f6",
        low: "#10b981",
        done: "#10b981",
        progress: "#eab308",
        // Camuflagem azul (aba Missões)
        "camo-base": "#0a1428",
        "camo-deep": "#050b1a",
        "camo-mid": "#15264a",
        "camo-light": "#2b4570",
        "camo-cyan": "#22d3ee",
        "camo-amber": "#fbbf24",
        "camo-line": "#1d3a6f",
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
