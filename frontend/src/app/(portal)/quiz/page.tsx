import Box from "@mui/material/Box";
import { QuizPage } from "@/features/quiz/components/QuizPage";

/**
 * P002 クイズ画面（Server Component）
 *
 * sessionId をクエリパラメータから受け取り、QuizPage に渡す。
 * 問題データはセッション作成時に一括取得済み（ローカル state で管理）。
 */
export default function QuizPageRoute() {
  return (
    <Box sx={{ p: 4, maxWidth: 600, mx: "auto" }}>
      <QuizPage />
    </Box>
  );
}
