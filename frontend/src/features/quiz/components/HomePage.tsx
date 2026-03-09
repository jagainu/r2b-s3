"use client";

import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import PetsIcon from "@mui/icons-material/Pets";
import { StartQuizButton } from "./StartQuizButton";
import { TodayQuizCard } from "./TodayQuizCard";
import { useUserStats } from "../hooks";

/** P001 ホーム画面の Client Component 部分 */
export function HomePage() {
  const { data: stats } = useUserStats();
  const learnedCount = stats?.total_correct_breeds ?? 0;

  return (
    <Box>
      {/* ヘッダー */}
      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 0.5 }}>
          <PetsIcon sx={{ color: "primary.main", fontSize: 22 }} />
          <Typography variant="h5" fontWeight={700} sx={{ color: "text.primary" }}>
            ねこ図鑑クイズ
          </Typography>
        </Box>
        <Typography variant="body2" color="text.secondary">
          {learnedCount > 0 ? `${learnedCount}種類の猫を覚えました` : "猫の種類を学んでみよう"}
        </Typography>
      </Box>

      {/* クイズ開始 */}
      <Box sx={{ mb: 3 }}>
        <StartQuizButton />
      </Box>

      {/* 今日の一匹 */}
      <TodayQuizCard />
    </Box>
  );
}
