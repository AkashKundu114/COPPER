/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        copper: {
          50:  "#fff8f1",
          100: "#ffedd8",
          200: "#ffd9b0",
          300: "#ffbf7d",
          400: "#ff9a45",
          500: "#ff7c1f",
          600: "#f05e0a",
          700: "#c7460a",
          800: "#9e3910",
          900: "#7f3110",
          950: "#451506",
        },
        dark: {
          900: "#0a0a0f",
          800: "#12121a",
          700: "#1a1a28",
          600: "#22223a",
          500: "#2d2d4a",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "glow": "glow 2s ease-in-out infinite alternate",
        "float": "float 6s ease-in-out infinite",
        "spin-slow": "spin 8s linear infinite",
        "fade-in": "fadeIn 0.3s ease-out",
        "slide-up": "slideUp 0.3s ease-out",
      },
      keyframes: {
        glow: {
          "0%": { boxShadow: "0 0 5px #ff7c1f, 0 0 10px #ff7c1f" },
          "100%": { boxShadow: "0 0 20px #ff7c1f, 0 0 40px #ff7c1f, 0 0 60px #ff7c1f" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-10px)" },
        },
        fadeIn: {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
        slideUp: {
          from: { opacity: "0", transform: "translateY(10px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
      },
      backgroundImage: {
        "grid-dark": "linear-gradient(rgba(255,124,31,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255,124,31,0.05) 1px, transparent 1px)",
      },
      backgroundSize: {
        "grid": "32px 32px",
      },
    },
  },
  plugins: [],
};
