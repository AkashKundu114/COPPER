export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        bg: {
          DEFAULT: "#000000",
          panel: "#111111",
          raised: "#1a1a1a",
        },
        border: {
          DEFAULT: "#333333",
          subtle: "#222222",
          neon: "transparent",
        },
        text: {
          DEFAULT: "#ffffff",
          muted: "#888888",
        },
        accent: {
          DEFAULT: "#e60000", // Swiss red
          hover: "#ff1a1a",
          copper: "#e60000",
        },
      },
      borderRadius: {
        'none': '0',
        'sm': '0',
        DEFAULT: '0',
        'md': '0',
        'lg': '0',
        'xl': '0',
        '2xl': '0',
        '3xl': '0',
        'full': '0',
      },
      boxShadow: {
        'sm': 'none',
        DEFAULT: 'none',
        'md': 'none',
        'lg': 'none',
        'xl': 'none',
        '2xl': 'none',
        'inner': 'none',
        neon: "none",
        "neon-copper": "none",
        hud: "none",
      },
      fontFamily: {
        display: ["Helvetica Neue", "Helvetica", "Arial", "sans-serif"],
        body: ["Helvetica Neue", "Helvetica", "Arial", "sans-serif"],
        mono: ["Courier New", "Courier", "monospace"],
      },
      keyframes: {
        "fade-in": { from: { opacity: "0" }, to: { opacity: "1" } },
        "slide-up": {
          from: { opacity: "0", transform: "translateY(8px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.2s ease-out",
        "slide-up": "slide-up 0.2s ease-out",
      },
    },
  },
  plugins: [],
};
