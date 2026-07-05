"use client";
import { createTheme } from "@mui/material/styles";

export const lightTheme = createTheme({
  palette: {
    mode: "light",
    primary: { main: "#0D9488" },      // teal
    secondary: { main: "#D97706" },    // amber
    error: { main: "#DC2626" },
    warning: { main: "#D97706" },
    info: { main: "#0284C7" },
    success: { main: "#059669" },
    background: { default: "#F4F6FB", paper: "#FFFFFF" },
    text: { primary: "#1E293B", secondary: "#64748B" },
    divider: "#E2E8F0",
  },
  typography: {
    fontFamily: "'Roboto', 'Segoe UI', sans-serif",
    h5: { fontWeight: 700 },
    h6: { fontWeight: 600 },
  },
  shape: { borderRadius: 12 },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundImage: "none",
          border: "1px solid #E2E8F0",
          boxShadow: "0 1px 3px rgba(15, 23, 42, 0.06)",
        },
      },
    },
  },
});
