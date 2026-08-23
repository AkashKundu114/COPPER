export default {
  content: ["./index.html", "./src*.{js,ts,jsx,tsx}"],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        bg: {
          DEFAULT: "#020617", // slate-950
          panel: "#0f172a", // slate-900
          raised: "#1e293b", // slate-800
        },
        border: {
          DEFAULT: "#1e293b", // slate-800
          subtle: "#0f172a", // slate-900
          neon: "rgba(14, 165, 233, 0.5)", // Sky 500
        },
        text: {
          DEFAULT: "#f8fafc", // slate-50
          muted: "#94a3b8", // slate-400
        },
        accent: {
          DEFAULT: "#0ea5e9", // Sky 500
          hover: "#38bdf8", // Sky 400
          copper: "#14b8a6", // Teal 500 (kept variable name 'copper' for compatibility)
        }
      },
      boxShadow: {
        'neon': '0 0 15px rgba(14, 165, 233, 0.4)',
        'neon-copper': '0 0 15px rgba(20, 184, 166, 0.4)',
        'hud': 'inset 0 0 20px rgba(14, 165, 233, 0.05)',
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
          "0%, 100%": { boxShadow: "0 0 15px rgba(14, 165, 233, 0.4)", borderColor: "rgba(14, 165, 233, 0.5)" },
          "50%": { boxShadow: "0 0 2px rgba(14, 165, 233, 0.1)", borderColor: "#1e293b" },
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
