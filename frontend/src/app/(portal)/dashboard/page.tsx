import Box from "@mui/material/Box";
import { HomePage } from "@/features/quiz/components/HomePage";

export default function DashboardPage() {
  return (
    <Box sx={{ px: 2, pt: 3, pb: 2, maxWidth: 640, mx: "auto" }}>
      <HomePage />
    </Box>
  );
}
