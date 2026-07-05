import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        surface: "#F4F6FB",
        panel: "#FFFFFF",
        accent: "#0D9488",
        danger: "#DC2626",
        warn: "#D97706",
        ok: "#059669",
      },
    },
  },
  plugins: [],
};
export default config;
