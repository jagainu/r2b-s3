import Box from "@mui/material/Box";
import { ExplanationPage } from "@/features/quiz";

/**
 * P003 解説画面（Server Component）
 *
 * クイズ回答後に表示される画面。
 * - 正解/不正解バナー
 * - 正解猫の写真・種類名・毛色・模様・毛の長さ
 * - 類似猫リスト（最大3件）
 * - 「次の問題へ」/「結果を見る」ボタン
 */
export default function ExplanationPageRoute() {
  return (
    <Box sx={{ p: 4 }}>
      <ExplanationPage />
    </Box>
  );
}
