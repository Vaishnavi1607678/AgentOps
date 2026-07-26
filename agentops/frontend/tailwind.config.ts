import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        base: "#090B10",
        surface: "#10141C",
        raised: "#171C26",
        line: "#232936",
        ink: "#E8ECF1",
        muted: "#7C8698",
        signal: "#5EEAD4",
        amber: "#F0B429",
        danger: "#FB7185",
        success: "#34D399",
      },
      fontFamily: {
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
        sans: ["Inter", "ui-sans-serif", "system-ui"],
      },
    },
  },
  plugins: [],
};
export default config;
