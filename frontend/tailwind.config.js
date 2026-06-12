/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Real copper-metal tones — warm amber-brown, not neon orange
        copper: {
          50:  "#fdf7f0",
          100: "#f8e8d4",
          200: "#f0ccaa",
          300: "#e5a870",
          400: "#d4843c",
          500: "#b87333",  // actual copper metal
          600: "#9a5e28",
          700: "#7a4820",
          800: "#5a3318",
          900: "#3a200e",
          950: "#1e0e06",
        },
        // Zinc surfaces — no blue tint, true neutral dark
        dark: {
          950: "#09090b",
          900: "#111113",
          800: "#1a1a1e",
          700: "#232328",
          600: "#2d2d33",
          500: "#3d3d45",
          400: "#52525c",
          300: "#71717c",
        },
      },
      fontFamily: {
        // Figtree: geometric sans, excellent legibility at small sizes
        sans: ["Figtree", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      fontSize: {
        "2xs": ["10px", { lineHeight: "14px" }],
      },
      animation: {
        "fade-in":    "fadeIn 0.2s ease-out",
        "slide-up":   "slideUp 0.25s ease-out",
        "slide-right":"slideRight 0.2s ease-out",
        "dot-bounce": "dotBounce 1.4s ease-in-out infinite",
        "pulse-slow": "pulse 2.5s cubic-bezier(0.4,0,0.6,1) infinite",
        "spin-slow":  "spin 8s linear infinite",
      },
      keyframes: {
        fadeIn: {
          from: { opacity: "0" },
          to:   { opacity: "1" },
        },
        slideUp: {
          from: { opacity: "0", transform: "translateY(6px)" },
          to:   { opacity: "1", transform: "translateY(0)" },
        },
        slideRight: {
          from: { opacity: "0", transform: "translateX(12px)" },
          to:   { opacity: "1", transform: "translateX(0)" },
        },
        dotBounce: {
          "0%, 80%, 100%": { transform: "translateY(0)" },
          "40%":            { transform: "translateY(-5px)" },
        },
      },
      // Subtle dot-grid background for the home splash
      backgroundImage: {
        "dot-grid": "radial-gradient(circle, rgba(255,255,255,0.06) 1px, transparent 1px)",
      },
      backgroundSize: {
        "dot-grid": "20px 20px",
      },
    },
  },
  plugins: [],
};
