import { Suspense } from "react";
import Box from "@mui/material/Box";
import CircularProgress from "@mui/material/CircularProgress";
import { QuizPage } from "@/features/quiz/components/QuizPage";

export default function QuizPageRoute() {
  return (
    <Box sx={{ p: 4, maxWidth: 600, mx: "auto" }}>
      <Suspense fallback={<Box sx={{ display: "flex", justifyContent: "center", pt: 8 }}><CircularProgress /></Box>}>
        <QuizPage />
      </Suspense>
    </Box>
  );
}
