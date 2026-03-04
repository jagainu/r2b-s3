import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import Skeleton from "@mui/material/Skeleton";
import { HomePage } from "@/features/quiz/components/HomePage";

/**
 * P001 ホーム画面（Server Component）
 *
 * - 「クイズを始める」ボタン -> POST /quiz/sessions -> P002 へ遷移
 * - 「今日の一匹」カード -> GET /quiz/today -> 1問クイズ表示
 * - 累計覚えた種類数バッジ -> Slice 5 で実装予定（スケルトン表示）
 */
export default function DashboardPage() {
  return (
    <Box sx={{ p: 4, maxWidth: 800, mx: "auto" }}>
      <Typography variant="h4" component="h1" fontWeight="bold" mb={4}>
        {"ホーム"}
      </Typography>

      <HomePage />

      {/* 累計覚えた種類数（Slice 5 で実装予定） */}
      <Box sx={{ mt: 4 }}>
        <Typography variant="subtitle1" color="text.secondary" mb={1}>
          {"覚えた種類数"}
        </Typography>
        <Skeleton variant="rounded" width={120} height={48} />
      </Box>
    </Box>
  );
}
