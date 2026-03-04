import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import Button from "@mui/material/Button";
import Link from "next/link";

export default function HomePage() {
  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "100vh",
        gap: 3,
        p: 2,
      }}
    >
      <Typography variant="h3" component="h1" fontWeight="bold">
        猫の種類学習アプリ
      </Typography>
      <Typography variant="h6" color="text.secondary">
        猫の種類を楽しく覚えよう
      </Typography>
      <Box sx={{ display: "flex", gap: 2 }}>
        <Button
          variant="contained"
          size="large"
          component={Link}
          href="/login"
        >
          ログイン
        </Button>
        <Button
          variant="outlined"
          size="large"
          component={Link}
          href="/dashboard"
        >
          ダッシュボード
        </Button>
      </Box>
    </Box>
  );
}
