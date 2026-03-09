"use client";

import { useRouter } from "next/navigation";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import CircularProgress from "@mui/material/CircularProgress";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import PetsIcon from "@mui/icons-material/Pets";
import { useLatestSession, useUserStats } from "../hooks";

export function ResultPage() {
  const router = useRouter();
  const { data: session, isLoading: sessionLoading } = useLatestSession("quiz");
  const { data: stats, isLoading: statsLoading } = useUserStats();

  if (sessionLoading || statsLoading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  const correctCount = session?.correct_count ?? 0;
  const incorrectCount = session?.incorrect_count ?? 0;
  const total = correctCount + incorrectCount;
  const correctRate = total > 0 ? Math.round((correctCount / total) * 100) : 0;
  const learnedCount = stats?.total_correct_breeds ?? 0;
  const isGood = correctRate >= 70;

  return (
    <Box sx={{ maxWidth: 480, mx: "auto", textAlign: "center" }}>
      {/* 結果ヘッダー */}
      <Box
        sx={{
          p: 4,
          mb: 3,
          borderRadius: 4,
          background: isGood
            ? "linear-gradient(135deg, #4A7C59 0%, #6AAE7A 100%)"
            : "linear-gradient(135deg, #C4570A 0%, #E8835A 100%)",
          boxShadow: isGood
            ? "0 8px 32px rgba(74, 124, 89, 0.3)"
            : "0 8px 32px rgba(196, 87, 10, 0.3)",
        }}
      >
        <Typography variant="overline" sx={{ color: "rgba(255,255,255,0.8)", letterSpacing: 3 }}>
          {isGood ? "素晴らしい！" : "もう一息！"}
        </Typography>
        <Typography
          variant="h1"
          fontWeight={700}
          sx={{ color: "#FFFFFF", lineHeight: 1, my: 1, fontSize: { xs: "4rem", sm: "5rem" } }}
        >
          {correctRate}%
        </Typography>
        <Typography variant="body1" sx={{ color: "rgba(255,255,255,0.85)" }}>
          {`${correctCount}問正解 / ${total}問`}
        </Typography>
      </Box>

      {/* 正解数・不正解数 */}
      <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 2, mb: 3 }}>
        <Box
          sx={{
            p: 2.5, borderRadius: 3, bgcolor: "background.paper",
            border: "1px solid rgba(44,35,24,0.07)",
            boxShadow: "0 2px 12px rgba(44,35,24,0.06)",
          }}
        >
          <Typography variant="h3" fontWeight={700} color="success.main">{correctCount}</Typography>
          <Typography variant="body2" color="text.secondary" fontWeight={500}>正解</Typography>
        </Box>
        <Box
          sx={{
            p: 2.5, borderRadius: 3, bgcolor: "background.paper",
            border: "1px solid rgba(44,35,24,0.07)",
            boxShadow: "0 2px 12px rgba(44,35,24,0.06)",
          }}
        >
          <Typography variant="h3" fontWeight={700} color="error.main">{incorrectCount}</Typography>
          <Typography variant="body2" color="text.secondary" fontWeight={500}>不正解</Typography>
        </Box>
      </Box>

      {/* 累計覚えた種類数 */}
      {learnedCount > 0 && (
        <Box
          sx={{
            p: 2, mb: 3, borderRadius: 3, bgcolor: "background.paper",
            border: "1px solid rgba(196, 87, 10, 0.2)",
            display: "flex", alignItems: "center", justifyContent: "center", gap: 1,
          }}
        >
          <PetsIcon sx={{ color: "primary.main" }} />
          <Typography fontWeight={700} color="primary.main">
            {`累計 ${learnedCount}種類をマスター！`}
          </Typography>
        </Box>
      )}

      {/* ボタン */}
      <Stack spacing={1.5} sx={{ pb: 2 }}>
        <Button variant="contained" size="large" onClick={() => router.push("/dashboard")} fullWidth>
          もう一度挑戦
        </Button>
        <Button variant="outlined" size="large" onClick={() => router.push("/cat-breeds")} fullWidth>
          図鑑を見る
        </Button>
      </Stack>
    </Box>
  );
}
