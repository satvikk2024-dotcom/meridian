import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        "bg-primary":     "var(--bg-primary)",
        "bg-surface":     "var(--bg-surface)",
        "bg-elevated":    "var(--bg-elevated)",
        "border-subtle":  "var(--border-subtle)",
        "border-default": "var(--border-default)",
        "fg-primary":     "var(--fg-primary)",
        "fg-secondary":   "var(--fg-secondary)",
        "fg-muted":       "var(--fg-muted)",
        "accent":         "var(--accent)",
        "accent-dim":     "var(--accent-dim)",
        "danger":         "var(--danger)",
        "warning":        "var(--warning)",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      fontSize: {
        micro: "11px",
        small: "13px",
        body:  "15px",
        h3:    "18px",
        h2:    "24px",
        h1:    "32px",
      },
      spacing: {
        // enforce 4px base scale — no arbitrary values
        "1": "4px",
        "2": "8px",
        "3": "12px",
        "4": "16px",
        "6": "24px",
        "8": "32px",
        "12": "48px",
        "16": "64px",
      },
    },
  },
  plugins: [],
};
export default config;
