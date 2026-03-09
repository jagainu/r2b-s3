import { createTheme } from "@mui/material/styles";

export const theme = createTheme({
  palette: {
    primary: {
      main: "#C4570A",
      light: "#E8905A",
      dark: "#8B3A00",
      contrastText: "#FFFFFF",
    },
    secondary: {
      main: "#6B7C5E",
      light: "#8FA882",
      dark: "#4A5740",
    },
    background: {
      default: "#FAF5EE",
      paper: "#FFFFFF",
    },
    text: {
      primary: "#2D2318",
      secondary: "#7A6558",
    },
    success: {
      main: "#4A7C59",
      light: "#D4EDD9",
      contrastText: "#FFFFFF",
    },
    error: {
      main: "#B94040",
      light: "#F5D5D5",
      contrastText: "#FFFFFF",
    },
  },
  typography: {
    fontFamily: [
      '"Zen Maru Gothic"',
      '"Noto Sans JP"',
      "-apple-system",
      "BlinkMacSystemFont",
      "sans-serif",
    ].join(","),
    h1: { fontWeight: 700 },
    h2: { fontWeight: 700 },
    h3: { fontWeight: 700 },
    h4: { fontWeight: 700 },
    h5: { fontWeight: 600 },
    h6: { fontWeight: 600 },
    button: { fontWeight: 600 },
  },
  shape: {
    borderRadius: 14,
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: "0 2px 16px rgba(44, 35, 24, 0.08)",
          border: "1px solid rgba(44, 35, 24, 0.07)",
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 28,
          textTransform: "none",
          fontWeight: 600,
          fontSize: "1rem",
          padding: "10px 24px",
        },
        containedPrimary: {
          background: "linear-gradient(135deg, #C4570A 0%, #E8835A 100%)",
          boxShadow: "0 4px 16px rgba(196, 87, 10, 0.25)",
          "&:hover": {
            background: "linear-gradient(135deg, #A8480A 0%, #CF6A42 100%)",
            boxShadow: "0 6px 20px rgba(196, 87, 10, 0.35)",
          },
        },
        outlinedPrimary: {
          borderWidth: 2,
          "&:hover": { borderWidth: 2 },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          fontWeight: 600,
          borderRadius: 8,
        },
      },
    },
    MuiLinearProgress: {
      styleOverrides: {
        root: {
          borderRadius: 6,
          height: 8,
          backgroundColor: "rgba(196, 87, 10, 0.12)",
        },
        bar: {
          borderRadius: 6,
          background: "linear-gradient(90deg, #C4570A 0%, #E8835A 100%)",
        },
      },
    },
    MuiBottomNavigation: {
      styleOverrides: {
        root: {
          backgroundColor: "rgba(250, 245, 238, 0.96)",
          borderTop: "1px solid rgba(44, 35, 24, 0.1)",
          backdropFilter: "blur(12px)",
        },
      },
    },
    MuiBottomNavigationAction: {
      styleOverrides: {
        root: {
          "&.Mui-selected": {
            color: "#C4570A",
          },
        },
      },
    },
  },
});
