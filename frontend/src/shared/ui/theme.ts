import { createTheme } from "@mui/material/styles";

export const theme = createTheme({
  palette: {
    primary: {
      main: "#FF6B35", // 猫っぽいオレンジ
    },
    secondary: {
      main: "#6B4C35",
    },
    background: {
      default: "#FAFAFA",
    },
  },
  typography: {
    fontFamily: [
      "Noto Sans JP",
      "-apple-system",
      "BlinkMacSystemFont",
      "Segoe UI",
      "sans-serif",
    ].join(","),
  },
  shape: {
    borderRadius: 8,
  },
});
