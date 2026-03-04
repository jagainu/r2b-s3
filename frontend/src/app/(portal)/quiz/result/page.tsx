import Box from "@mui/material/Box";
import { ResultPage } from "@/features/quiz";

/**
 * P006 結果画面（Server Component）
 *
 * クイズ10問完了後に表示される画面。
 * - 正答率・正解数・不正解数
 * - 累計覚えた種類数バッジ
 * - 「もう一度」「図鑑へ」「ホームへ」ボタン
 */
export default function ResultPageRoute() {
  return (
    <Box sx={{ p: 4 }}>
      <ResultPage />
    </Box>
  );
}
