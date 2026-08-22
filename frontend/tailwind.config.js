export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        bg: {
          DEFAULT: "#09090b", // true black/zinc-950 for deeper OS feel
          panel: "#18181b", // zinc-900
          raised: "#27272a", // zinc-800
        },
        border: {
          DEFAULT: "#27272a",
          subtle: "#18181b",
          neon: "rgba(6, 182, 212, 0.5)", // Cyan border
        },
        text: {
          DEFAULT: "#fafafa",
          muted: "#a1a1aa",
        },
        accent: {
          DEFAULT: "#06b6d4", // Cyan 500
          hover: "#22d3ee", // Cyan 400
          copper: "#f59e0b", // Amber 500
        }
      },
      boxShadow: {
        'neon': '0 0 15px rgba(6, 182, 212, 0.4)',
        'neon-copper': '0 0 15px rgba(245, 158, 11, 0.4)',
        'hud': 'inset 0 0 20px rgba(6, 182, 212, 0.05)',
      },
      fontFamily: {
        display: ["Inter", "system-ui", "sans-serif"],
        body: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "IBM Plex Mono", "monospace"],
      },
      keyframes: {
        "fade-in": { from: { opacity: "0" }, to: { opacity: "1" } },
        "slide-up": {
          from: { opacity: "0", transform: "translateY(8px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "pulse-glow": {
          "0%, 100%": { boxShadow: "0 0 15px rgba(6, 182, 212, 0.4)", borderColor: "rgba(6, 182, 212, 0.5)" },
          "50%": { boxShadow: "0 0 2px rgba(6, 182, 212, 0.1)", borderColor: "#27272a" },
        }
      },
      animation: {
        "fade-in": "fade-in 0.3s ease-out",
        "slide-up": "slide-up 0.3s ease-out",
        "pulse-glow": "pulse-glow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
    },
  },
  plugins: [],
};
