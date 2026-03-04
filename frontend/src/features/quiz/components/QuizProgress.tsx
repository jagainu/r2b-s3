"use client";

import Box from "@mui/material/Box";
import LinearProgress from "@mui/material/LinearProgress";
import Typography from "@mui/material/Typography";

interface QuizProgressProps {
  currentQuestion: number;
  totalQuestions: number;
}

/** P002 クイズ画面: 問題番号進捗表示（例: 3/10） */
export function QuizProgress({
  currentQuestion,
  totalQuestions,
}: QuizProgressProps) {
  const progress = (currentQuestion / totalQuestions) * 100;

  return (
    <Box sx={{ mb: 3 }}>
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          mb: 1,
        }}
      >
        <Typography variant="body2" color="text.secondary">
          {"問題"}
        </Typography>
        <Typography variant="h6" fontWeight="bold">
          {`${currentQuestion} / ${totalQuestions}`}
        </Typography>
      </Box>
      <LinearProgress
        variant="determinate"
        value={progress}
        sx={{ height: 8, borderRadius: 4 }}
      />
    </Box>
  );
}
