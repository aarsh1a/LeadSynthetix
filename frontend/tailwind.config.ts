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
        surface: {
          900: "#0d1117",
          800: "#161b22",
          700: "#21262d",
          600: "#30363d",
          500: "#484f58",
        },
        accent: {
          teal: "#2dd4bf",
          cyan: "#22d3ee",
          emerald: "#34d399",
          amber: "#fbbf24",
          rose: "#fb7185",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      keyframes: {
        "fade-in": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "fade-in-scale": {
          "0%": { opacity: "0", transform: "scale(0.96)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        "slide-up": {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        stagger: {
          "0%": { opacity: "0", transform: "translateX(-8px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.4s ease-out forwards",
        "fade-in-scale": "fade-in-scale 0.35s ease-out forwards",
        "slide-up": "slide-up 0.5s ease-out forwards",
        stagger: "stagger 0.4s ease-out forwards",
        shimmer: "shimmer 1.5s ease-in-out infinite",
      },
      boxShadow: {
        glow: "0 0 24px -4px rgba(45, 212, 191, 0.15)",
        "glow-amber": "0 0 24px -4px rgba(251, 191, 36, 0.2)",
        "glow-rose": "0 0 24px -4px rgba(251, 113, 133, 0.2)",
      },
    },
  },
  plugins: [],
};
export default config;
