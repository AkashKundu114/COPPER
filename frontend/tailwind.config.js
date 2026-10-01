export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // ── Surface Ladder (Warm Noir) ──────────────────────────
        canvas:           { DEFAULT: "#0A0808" },
        surface: {
          base:           "#121010",
          elevated:       "#1A1716",
          hover:          "#231F1D",
          active:         "#2D2724",
          spotlight:      "#362F2B",
        },

        // ── Borders (Alpha-based hairlines) ─────────────────────
        border: {
          DEFAULT:        "rgba(255, 255, 255, 0.05)",
          subtle:         "rgba(255, 255, 255, 0.08)",
          highlight:      "rgba(255, 255, 255, 0.14)",
          copper:         "rgba(212, 132, 90, 0.40)",
        },

        // ── Text Hierarchy ──────────────────────────────────────
        text: {
          DEFAULT:        "#F2EDEA",
          secondary:      "#9A918B",
          tertiary:       "#5C5550",
          inverse:        "#0A0808",
        },

        // ── Brand Accent — Copper ───────────────────────────────
        copper: {
          DEFAULT:        "#D4845A",
          bright:         "#E8A47A",
          dim:            "#9A6040",
          subtle:         "rgba(212, 132, 90, 0.12)",
          glow:           "rgba(212, 132, 90, 0.25)",
        },

        // ── Status / Semantic ───────────────────────────────────
        success:          { DEFAULT: "#5FC992", dim: "rgba(95, 201, 146, 0.12)" },
        warning:          { DEFAULT: "#FFB84D", dim: "rgba(255, 184, 77, 0.12)" },
        danger:           { DEFAULT: "#F06060", dim: "rgba(240, 96, 96, 0.12)" },
        info:             { DEFAULT: "#6BB3E0", dim: "rgba(107, 179, 224, 0.12)" },

        // ── Agent Tier Colors ───────────────────────────────────
        tier: {
          core:           "#4ADE9A",
          code:           "#38BCD8",
          os:             "#5B93F0",
          vision:         "#E06E9E",
          web:            "#E8A840",
          audio:          "#9B6DD8",
        },
      },

      borderRadius: {
        xs:               "2px",
        sm:               "4px",
        DEFAULT:          "6px",
        md:               "6px",
        lg:               "8px",
        xl:               "12px",
        "2xl":            "16px",
        "3xl":            "20px",
        full:             "9999px",
      },

      boxShadow: {
        sm:               "0 1px 2px rgba(0, 0, 0, 0.3)",
        DEFAULT:          "0 2px 6px rgba(0, 0, 0, 0.35)",
        md:               "0 4px 12px rgba(0, 0, 0, 0.40)",
        lg:               "0 8px 24px rgba(0, 0, 0, 0.45)",
        xl:               "0 16px 48px rgba(0, 0, 0, 0.50)",
        "inner-highlight":"inset 0 1px 0 0 rgba(255, 255, 255, 0.06)",
        "elevation-card": "0 1px 3px rgba(0, 0, 0, 0.5), inset 0 1px 0 0 rgba(255, 255, 255, 0.06)",
        "elevation-modal":"0 16px 70px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(255, 255, 255, 0.08)",
        "glow-copper":    "0 0 24px -6px rgba(212, 132, 90, 0.30)",
      },

      fontFamily: {
        sans:   ["'Inter Variable'", "Inter", "-apple-system", "BlinkMacSystemFont", "'Segoe UI'", "sans-serif"],
        mono:   ["'Geist Mono Variable'", "'Geist Mono'", "'JetBrains Mono'", "Menlo", "monospace"],
        brand:  ["'Moon Walk'", "'Inter Variable'", "sans-serif"],
      },

      fontSize: {
        "2xs":    ["0.625rem",  { lineHeight: "0.875rem",  letterSpacing: "0.02em"   }],
        "xs":     ["0.6875rem", { lineHeight: "1rem",      letterSpacing: "0.01em"   }],
        "caption":["0.75rem",   { lineHeight: "1rem",      letterSpacing: "0"        }],
        "sm":     ["0.8125rem", { lineHeight: "1.125rem",  letterSpacing: "-0.005em" }],
        "base":   ["0.875rem",  { lineHeight: "1.25rem",   letterSpacing: "-0.01em"  }],
        "md":     ["1rem",      { lineHeight: "1.5rem",    letterSpacing: "-0.015em" }],
        "lg":     ["1.125rem",  { lineHeight: "1.625rem",  letterSpacing: "-0.02em"  }],
        "xl":     ["1.25rem",   { lineHeight: "1.75rem",   letterSpacing: "-0.025em" }],
        "2xl":    ["1.5rem",    { lineHeight: "2rem",      letterSpacing: "-0.03em"  }],
        "3xl":    ["1.875rem",  { lineHeight: "2.25rem",   letterSpacing: "-0.035em" }],
      },

      keyframes: {
        "fade-in": {
          from: { opacity: "0" },
          to:   { opacity: "1" },
        },
        "slide-up": {
          from: { opacity: "0", transform: "translateY(6px)" },
          to:   { opacity: "1", transform: "translateY(0)"   },
        },
        "pulse-dot": {
          "0%, 100%": { opacity: "1" },
          "50%":      { opacity: "0.4" },
        },
      },

      animation: {
        "fade-in":   "fade-in 150ms cubic-bezier(0.16, 1, 0.3, 1)",
        "slide-up":  "slide-up 180ms cubic-bezier(0.16, 1, 0.3, 1)",
        "pulse-dot": "pulse-dot 2s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
