import { Suspense } from "react";
import Box from "@mui/material/Box";
import CircularProgress from "@mui/material/CircularProgress";
import { ExplanationPage } from "@/features/quiz";

export default function ExplanationPageRoute() {
  return (
    <Box sx={{ p: 4 }}>
      <Suspense fallback={<Box sx={{ display: "flex", justifyContent: "center", pt: 8 }}><CircularProgress /></Box>}>
        <ExplanationPage />
      </Suspense>
    </Box>
  );
}
