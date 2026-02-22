import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        glass: {
          bg: "rgba(255, 255, 255, 0.08)",
          border: "rgba(255, 255, 255, 0.18)",
          highlight: "rgba(255, 255, 255, 0.25)",
        },
        accent: {
          cyan: "#22d3ee",
          violet: "#a78bfa",
          emerald: "#34d399",
        },
      },
      backdropBlur: {
        glass: "12px",
        glassStrong: "24px",
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "gradient-mesh":
          "radial-gradient(at 40% 20%, hsla(192, 100%, 60%, 0.15) 0px, transparent 50%), radial-gradient(at 80% 0%, hsla(263, 70%, 70%, 0.12) 0px, transparent 50%), radial-gradient(at 0% 50%, hsla(160, 70%, 60%, 0.1) 0px, transparent 50%)",
      },
      animation: {
        "fade-in": "fadeIn 0.4s ease-out",
        "slide-up": "slideUp 0.4s ease-out",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
