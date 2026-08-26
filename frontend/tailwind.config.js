export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        bg: { DEFAULT: "#0B0C0E", panel: "#15171A", raised: "#1D2023" },
        border: { DEFAULT: "#26292E", subtle: "#1C1E22", strong: "#34383F" },
        text: { DEFAULT: "#EDEDEA", muted: "#8B8D93" },

        // Legacy-token aliases — several components still reference an
        // earlier "void/ink" naming that was dropped from this config.
        // Aliasing them here means those components render correctly
        // with zero edits, instead of silently emitting no styles.
        void: { DEFAULT: "#0B0C0E", panel: "#15171A", raised: "#1D2023" },
        ink: {
          DEFAULT: "#EDEDEA",
          primary: "#EDEDEA",
          secondary: "#B4B6BC",
          faint: "#6C6F76",
        },

        // Copper — full ramp so every existing `sky-050…950` / `cyan-050…950`
        // utility class can be mechanically renamed to `accent-050…950`
        // (via the codemod script) and still resolve to a real color.
        accent: {
          DEFAULT: "#C97C4C",
          hover: "#DB9563",
          dim: "#8A5636",
          copper: "#C97C4C",
          50: "#FBF2EA",
          100: "#F5E2CF",
          200: "#EAC29C",
          300: "#DFA36C",
          400: "#D38F53",
          500: "#C97C4C",
          600: "#AD6339",
          700: "#8A5636",
          800: "#6B4229",
          900: "#4A2D1C",
          950: "#2E1B11",
        },

        // Molten copper — warnings / "hot" states (replaces amber).
        molten: {
          DEFAULT: "#FF7A45",
          50: "#FFF4EC",
          100: "#FFE3CE",
          200: "#FFC49B",
          300: "#FFA268",
          400: "#FF7A45",
          500: "#F2602A",
          600: "#D14A1C",
          700: "#A83816",
          800: "#7A2A12",
          900: "#4F1B0C",
          950: "#301007",
        },

        // Verdigris — copper's oxidation patina; success/positive (replaces emerald).
        verdigris: {
          DEFAULT: "#5FA88F",
          dim: "#3F6F5F",
          50: "#EEF7F4",
          100: "#D7EDE5",
          200: "#AEDBCB",
          300: "#84C5AE",
          400: "#5FA88F",
          500: "#4C8E77",
          600: "#3F6F5F",
          700: "#325A4C",
          800: "#274539",
          900: "#1B2E27",
          950: "#101E19",
        },

        // Danger — replaces rose/red.
        danger: {
          DEFAULT: "#E5484D",
          50: "#FDEEEE",
          100: "#FBD8D9",
          200: "#F5B0B2",
          300: "#EE8689",
          400: "#E86266",
          500: "#E5484D",
          600: "#C43439",
          700: "#9C282C",
          800: "#711D20",
          900: "#4A1315",
          950: "#2E0B0C",
        },
      },
      borderRadius: {
        none: "0px",
        sm: "6px",
        DEFAULT: "8px",
        md: "10px",
        lg: "12px",
        xl: "16px",
        "2xl": "20px",
        "3xl": "28px",
        full: "9999px",
      },
      boxShadow: {
        sm: "0 1px 2px rgba(0,0,0,0.35)",
        DEFAULT: "0 2px 8px rgba(0,0,0,0.35)",
        md: "0 4px 16px rgba(0,0,0,0.40)",
        lg: "0 8px 32px rgba(0,0,0,0.45)",
        xl: "0 16px 48px rgba(0,0,0,0.50)",
        inner: "inset 0 1px 2px rgba(0,0,0,0.30)",
        neon: "0 0 0 1px rgba(201,124,76,0.45)",
        "neon-copper": "0 0 24px rgba(201,124,76,0.16)",
        hud: "0 1px 0 rgba(255,255,255,0.03) inset, 0 8px 24px rgba(0,0,0,0.35)",
      },
      fontFamily: {
        display: ["'Space Grotesk'", "Inter", "'Helvetica Neue'", "sans-serif"],
        body: ["Inter", "'Helvetica Neue'", "Helvetica", "Arial", "sans-serif"],
        mono: ["'IBM Plex Mono'", "'Courier New'", "Courier", "monospace"],
      },
      keyframes: {
        "fade-in": { from: { opacity: "0" }, to: { opacity: "1" } },
        "slide-up": {
          from: { opacity: "0", transform: "translateY(8px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        trace: { "0%": { backgroundPosition: "0% 0" }, "100%": { backgroundPosition: "200% 0" } },
      },
      animation: {
        "fade-in": "fade-in 0.2s ease-out",
        "slide-up": "slide-up 0.2s ease-out",
        trace: "trace 2.4s linear infinite",
      },
    },
  },
  plugins: [],
};
