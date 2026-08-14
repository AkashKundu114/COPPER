export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        bg: {
          DEFAULT: "#18181b", // zinc-900
          panel: "#27272a", // zinc-800
          raised: "#3f3f46", // zinc-700
        },
        border: {
          DEFAULT: "#3f3f46", // zinc-700
          subtle: "#27272a", // zinc-800
        },
        text: {
          DEFAULT: "#f4f4f5", // zinc-100
          muted: "#a1a1aa", // zinc-400
        },
        accent: {
          DEFAULT: "#e4e4e7", // zinc-200
          hover: "#ffffff",
        }
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
        }
      },
      animation: {
        "fade-in": "fade-in 0.3s ease-out",
        "slide-up": "slide-up 0.3s ease-out",
      },
    },
  },
  plugins: [],
};
