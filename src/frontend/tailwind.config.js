// Design tokens from docs/inputs/DESIGN.md (Zest Minimalist Workbench Design System v3.0.0).
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#F8F9FA",
        subtle: "#F1F3F5",
        line: "#E5E7EB",
        strong: "#D1D5DB",
        muted: "#6B7280",
        secondary: "#374151",
        ink: "#111827",
        brand: { DEFAULT: "#381E72", hover: "#2C1659", active: "#231048", tint: "#F3EEFC" },
        ok: { DEFAULT: "#10B981", surface: "#ECFDF5", border: "#A7F3D0", text: "#065F46" },
        warn: { DEFAULT: "#D97706", surface: "#FFFBEB" },
        err: { DEFAULT: "#DC2626", surface: "#FEF2F2", border: "#FCA5A5" },
        dim: { DEFAULT: "#9CA3AF", surface: "#F3F4F6" },
        celebrate: { from: "#1E0A3C", to: "#3B1464", text: "#D8B4FE", seal: "#7C3AED" },
        chart: { history: "#381E72", trend: "#D97706", culinary: "#10B981", persona: "#64748B" },
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", '"Segoe UI"', "Roboto", "sans-serif"],
        display: ['"Plus Jakarta Sans"', "Inter", "sans-serif"],
        mono: ['"JetBrains Mono"', '"SF Mono"', "Menlo", "monospace"],
      },
      borderRadius: { xs: "4px", sm: "6px", md: "8px", lg: "12px", xl: "16px", "2xl": "24px" },
      boxShadow: {
        sm: "0 1px 2px rgba(0, 0, 0, 0.04)",
        card: "0 2px 6px -1px rgba(0, 0, 0, 0.06), 0 1px 3px -1px rgba(0, 0, 0, 0.03)",
        modal: "0 20px 35px -5px rgba(0, 0, 0, 0.15), 0 10px 15px -5px rgba(0, 0, 0, 0.05)",
      },
      zIndex: { 100: "100" },
    },
  },
  plugins: [],
};
