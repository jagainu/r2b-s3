"use client";

import { useSearchParams, useRouter } from "next/navigation";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useCatBreedDetail, SimilarCats } from "@/features/cat-breeds";
import { useFinalizeSession } from "../hooks";

/**
 * P003 解説画面の Client Component
 *
 * クイズ回答後に表示する。
 * - 正解/不正解バナー
 * - 正解猫の写真・種類名・毛色・模様・毛の長さ
 * - 類似猫リスト（最大3件）
 * - 「次の問題へ」ボタン（10問完了時は「結果を見る」）
 */
export function ExplanationPage() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const isCorrect = searchParams.get("isCorrect") === "true";
  const correctCatId = searchParams.get("correctCatId") ?? "";
  const sessionId = searchParams.get("sessionId") ?? "";
  const questionIndex = parseInt(searchParams.get("questionIndex") ?? "0", 10);
  const totalQuestions = parseInt(
    searchParams.get("totalQuestions") ?? "10",
    10,
  );
  const source = searchParams.get("source") ?? "quiz";

  const { data: breed, isLoading: breedLoading } =
    useCatBreedDetail(correctCatId);
  const { mutate: finalize, isPending: finalizing } = useFinalizeSession();

  const isLastQuestion = questionIndex >= totalQuestions - 1;

  const handleNext = () => {
    if (isLastQuestion) {
      // 10問完了 → finalize → 結果画面へ
      if (source === "today") {
        // today はセッション1問のみなので、finalize してホームへ
        finalize(sessionId, {
          onSuccess: () => {
            router.push("/dashboard");
          },
          onError: () => {
            // finalize 失敗時もホームへ戻す
            router.push("/dashboard");
          },
        });
      } else {
        finalize(sessionId, {
          onSuccess: () => {
            router.push(`/quiz/result?sessionId=${sessionId}`);
          },
          onError: () => {
            // finalize 失敗時も結果画面へ（Slice 5 で実装）
            router.push(`/quiz/result?sessionId=${sessionId}`);
          },
        });
      }
    } else {
      // 次の問題へ（QuizPage に戻る）
      const nextIndex = questionIndex + 1;
      router.push(`/quiz?sessionId=${sessionId}&questionIndex=${nextIndex}`);
    }
  };

  if (breedLoading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 600, mx: "auto", py: 3 }}>
      {/* 正解/不正解バナー */}
      <Box
        sx={{
          p: 2,
          mb: 3,
          borderRadius: 2,
          textAlign: "center",
          backgroundColor: isCorrect ? "success.light" : "error.light",
          color: isCorrect ? "success.contrastText" : "error.contrastText",
        }}
      >
        <Typography variant="h5" fontWeight="bold">
          {isCorrect ? "正解!" : "不正解"}
        </Typography>
      </Box>

      {/* 正解猫の情報 */}
      {breed && (
        <Box>
          {/* 写真 */}
          {breed.photos.length > 0 && (
            <Box
              component="img"
              src={breed.photos[0].url}
              alt={breed.name}
              sx={{
                width: "100%",
                maxHeight: 300,
                objectFit: "cover",
                borderRadius: 2,
                mb: 2,
              }}
            />
          )}

          {/* 種類名 */}
          <Typography variant="h4" fontWeight="bold" gutterBottom>
            {breed.name}
          </Typography>

          {/* 特徴 */}
          <Typography variant="h6" gutterBottom>
            {"特徴"}
          </Typography>
          <Stack
            direction="row"
            spacing={1}
            flexWrap="wrap"
            useFlexGap
            sx={{ mb: 2 }}
          >
            <Chip
              label={`毛色: ${breed.coat_color.name}`}
              color="primary"
              variant="outlined"
            />
            <Chip
              label={`模様: ${breed.coat_pattern.name}`}
              color="secondary"
              variant="outlined"
            />
            <Chip
              label={`毛の長さ: ${breed.coat_length.name}`}
              variant="outlined"
            />
          </Stack>

          {/* 類似猫 */}
          <SimilarCats breedId={correctCatId} />
        </Box>
      )}

      {/* 次の問題へ / 結果を見る */}
      <Box sx={{ mt: 4, textAlign: "center" }}>
        <Button
          variant="contained"
          size="large"
          onClick={handleNext}
          disabled={finalizing}
          sx={{ minWidth: 200 }}
        >
          {finalizing && <CircularProgress size={20} sx={{ mr: 1 }} />}
          {isLastQuestion
            ? source === "today"
              ? "ホームに戻る"
              : "結果を見る"
            : "次の問題へ"}
        </Button>
      </Box>
    </Box>
  );
}
