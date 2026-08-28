/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#000000",
        surface: {
          DEFAULT: "#0D1117",
          elevated: "#161B22",
          card: "rgba(13, 17, 23, 0.88)",
        },
        primary: {
          DEFAULT: "#F0F6FC",
          muted: "#8B949E",
          subtle: "#30363D",
        },
        accent: {
          DEFAULT: "#F0B90B",
          hover: "#D9A404",
          subtle: "rgba(240, 185, 11, 0.12)",
        },
        profit: {
          DEFAULT: "#0ECB81",
          subtle: "rgba(14, 203, 129, 0.12)",
          border: "rgba(14, 203, 129, 0.32)",
        },
        loss: {
          DEFAULT: "#F6465D",
          subtle: "rgba(246, 70, 93, 0.12)",
          border: "rgba(246, 70, 93, 0.32)",
        },
        warning: {
          DEFAULT: "#F59E0B",
          subtle: "rgba(245, 158, 11, 0.12)",
        },
        glass: {
          panel: "rgba(13, 17, 23, 0.85)",
          border: "rgba(240, 246, 252, 0.10)",
          hover: "rgba(22, 27, 34, 0.95)",
        },
      },
      boxShadow: {
        glass: "0 4px 20px -2px rgba(0, 0, 0, 0.6), 0 2px 6px -1px rgba(0, 0, 0, 0.4)",
        "glass-hover": "0 10px 25px -3px rgba(0, 0, 0, 0.8), 0 0 15px rgba(240, 185, 11, 0.15)",
        elevation: "0 20px 40px -15px rgba(0, 0, 0, 0.9)",
        glow: "0 0 20px -5px rgba(240, 185, 11, 0.25)",
        "glow-green": "0 0 20px -5px rgba(14, 203, 129, 0.25)",
        "glow-red": "0 0 20px -5px rgba(246, 70, 93, 0.25)",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
        mono: ["JetBrains Mono", "SFMono-Regular", "Menlo", "monospace"],
      },
    },
  },
  plugins: [],
};
