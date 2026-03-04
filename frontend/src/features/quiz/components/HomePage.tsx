"use client";

import Box from "@mui/material/Box";
import Chip from "@mui/material/Chip";
import { StartQuizButton } from "./StartQuizButton";
import { TodayQuizCard } from "./TodayQuizCard";
import { useUserStats } from "../hooks";

/** P001 ホーム画面の Client Component 部分 */
export function HomePage() {
  const { data: stats } = useUserStats();
  const learnedCount = stats?.total_correct_breeds ?? 0;

  return (
    <Box>
      {/* 統計バッジ */}
      {learnedCount > 0 && (
        <Box sx={{ display: "flex", justifyContent: "center", mb: 2 }}>
          <Chip
            label={`${learnedCount}種類覚えた!`}
            color="primary"
            variant="filled"
            sx={{ fontSize: "1rem", py: 2, px: 1 }}
          />
        </Box>
      )}

      {/* クイズ開始 */}
      <Box sx={{ display: "flex", justifyContent: "center", mb: 4 }}>
        <StartQuizButton />
      </Box>

      {/* 今日の一匹 */}
      <Box sx={{ display: "flex", justifyContent: "center" }}>
        <TodayQuizCard />
      </Box>
    </Box>
  );
}
