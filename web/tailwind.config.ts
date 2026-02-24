import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        // FF7 Mako / Materia palette
        mako: {
          50: "#e8fff5",
          100: "#b8ffdf",
          200: "#7affc4",
          300: "#3dffa8",
          400: "#00ff8c",
          500: "#00e07a",  // Primary green (Mako energy)
          600: "#00b863",
          700: "#008f4c",
          800: "#006636",
          900: "#003d20",
        },
        ff: {
          dark: "#0a0e1a",       // Deep space black
          panel: "#111827",      // Panel background
          border: "#1e3a5f",     // Blue border (FF7 menu)
          "border-light": "#2d5a8e",
          highlight: "#3b82f6",  // Selection blue
          text: "#c8d6e5",       // Muted text
          "text-bright": "#e8ecf1",
          gold: "#f5c842",       // Gil / materia gold
          red: "#ff4757",        // HP low / damage
          blue: "#4fc3f7",       // MP / magic
        },
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', "Menlo", "Monaco", "monospace"],
      },
      boxShadow: {
        ff: "0 0 0 1px #1e3a5f, 0 0 15px rgba(0, 224, 122, 0.1)",
        "ff-glow": "0 0 20px rgba(0, 224, 122, 0.2), 0 0 40px rgba(0, 224, 122, 0.1)",
      },
    },
  },
  plugins: [],
};

export default config;
