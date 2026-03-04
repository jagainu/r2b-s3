"use client";

import { useRouter } from "next/navigation";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import CircularProgress from "@mui/material/CircularProgress";
import Divider from "@mui/material/Divider";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useLatestSession, useUserStats } from "../hooks";

/**
 * P006 結果画面の Client Component
 *
 * クイズ10問完了後に表示する。
 * - 正答率・正解数・不正解数を大きく表示
 * - 累計覚えた種類数バッジ
 * - 「もう一度」「図鑑へ」「ホームへ」ボタン
 */
export function ResultPage() {
  const router = useRouter();
  const { data: session, isLoading: sessionLoading } =
    useLatestSession("quiz");
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

  return (
    <Box sx={{ maxWidth: 500, mx: "auto", py: 4, textAlign: "center" }}>
      {/* 正答率 */}
      <Typography variant="h6" color="text.secondary" gutterBottom>
        {"正答率"}
      </Typography>
      <Typography
        variant="h1"
        fontWeight="bold"
        color={correctRate >= 70 ? "success.main" : "warning.main"}
        sx={{ mb: 1 }}
      >
        {correctRate}%
      </Typography>

      {/* 正解数・不正解数 */}
      <Stack
        direction="row"
        spacing={4}
        justifyContent="center"
        sx={{ mb: 3 }}
      >
        <Box>
          <Typography variant="h4" fontWeight="bold" color="success.main">
            {correctCount}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {"正解"}
          </Typography>
        </Box>
        <Box>
          <Typography variant="h4" fontWeight="bold" color="error.main">
            {incorrectCount}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {"不正解"}
          </Typography>
        </Box>
      </Stack>

      <Divider sx={{ mb: 3 }} />

      {/* 累計覚えた種類数 */}
      <Box
        sx={{
          p: 2,
          mb: 4,
          borderRadius: 2,
          backgroundColor: "primary.light",
          color: "primary.contrastText",
        }}
      >
        <Typography variant="h5" fontWeight="bold">
          {`${learnedCount}種類覚えた!`}
        </Typography>
        <Typography variant="body2">{"累計正解猫種数"}</Typography>
      </Box>

      {/* ボタン */}
      <Stack spacing={2}>
        <Button
          variant="contained"
          size="large"
          onClick={() => router.push("/dashboard")}
          fullWidth
        >
          {"もう一度挑戦"}
        </Button>
        <Button
          variant="outlined"
          size="large"
          onClick={() => router.push("/cat-breeds")}
          fullWidth
        >
          {"図鑑へ"}
        </Button>
        <Button
          variant="text"
          size="large"
          onClick={() => router.push("/dashboard")}
          fullWidth
        >
          {"ホームへ"}
        </Button>
      </Stack>
    </Box>
  );
}
