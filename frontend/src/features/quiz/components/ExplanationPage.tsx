"use client";

import { useSearchParams, useRouter } from "next/navigation";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import CheckCircleRoundedIcon from "@mui/icons-material/CheckCircleRounded";
import CancelRoundedIcon from "@mui/icons-material/CancelRounded";
import { useCatBreedDetail, SimilarCats } from "@/features/cat-breeds";
import { useFinalizeSession } from "../hooks";

export function ExplanationPage() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const isCorrect = searchParams.get("isCorrect") === "true";
  const correctCatId = searchParams.get("correctCatId") ?? "";
  const sessionId = searchParams.get("sessionId") ?? "";
  const questionIndex = parseInt(searchParams.get("questionIndex") ?? "0", 10);
  const totalQuestions = parseInt(searchParams.get("totalQuestions") ?? "10", 10);
  const source = searchParams.get("source") ?? "quiz";

  const { data: breed, isLoading: breedLoading } = useCatBreedDetail(correctCatId);
  const { mutate: finalize, isPending: finalizing } = useFinalizeSession();

  const isLastQuestion = questionIndex >= totalQuestions - 1;

  const handleNext = () => {
    if (isLastQuestion) {
      if (source === "today") {
        finalize(sessionId, {
          onSuccess: () => router.push("/dashboard"),
          onError: () => router.push("/dashboard"),
        });
      } else {
        finalize(sessionId, {
          onSuccess: () => router.push(`/quiz/result?sessionId=${sessionId}`),
          onError: () => router.push(`/quiz/result?sessionId=${sessionId}`),
        });
      }
    } else {
      router.push(`/quiz?sessionId=${sessionId}&questionIndex=${questionIndex + 1}`);
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
    <Box sx={{ maxWidth: 600, mx: "auto" }}>
      {/* 正解/不正解バナー */}
      <Box
        sx={{
          p: 2.5,
          mb: 3,
          borderRadius: 3,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 1.5,
          background: isCorrect
            ? "linear-gradient(135deg, #4A7C59 0%, #6AAE7A 100%)"
            : "linear-gradient(135deg, #B94040 0%, #E06060 100%)",
          boxShadow: isCorrect
            ? "0 4px 16px rgba(74, 124, 89, 0.35)"
            : "0 4px 16px rgba(185, 64, 64, 0.35)",
        }}
      >
        {isCorrect ? (
          <CheckCircleRoundedIcon sx={{ color: "#FFFFFF", fontSize: 28 }} />
        ) : (
          <CancelRoundedIcon sx={{ color: "#FFFFFF", fontSize: 28 }} />
        )}
        <Typography variant="h5" fontWeight={700} sx={{ color: "#FFFFFF" }}>
          {isCorrect ? "正解！" : "不正解"}
        </Typography>
      </Box>

      {/* 正解猫の情報 */}
      {breed && (
        <Box>
          {breed.photos.length > 0 && (
            <Box
              component="img"
              src={breed.photos[0].url}
              alt={breed.name}
              sx={{
                width: "100%",
                maxHeight: 280,
                objectFit: "cover",
                borderRadius: 3,
                mb: 2,
              }}
            />
          )}

          <Typography variant="h4" fontWeight={700} gutterBottom>
            {breed.name}
          </Typography>

          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap sx={{ mb: 2.5 }}>
            <Chip label={`毛色: ${breed.coat_color.name}`} color="primary" variant="outlined" size="small" />
            <Chip label={`模様: ${breed.coat_pattern.name}`} color="secondary" variant="outlined" size="small" />
            <Chip label={`毛の長さ: ${breed.coat_length.name}`} variant="outlined" size="small" />
          </Stack>

          <SimilarCats breedId={correctCatId} />
        </Box>
      )}

      {/* 次の問題へ / 結果を見る */}
      <Box sx={{ mt: 4, pb: 2 }}>
        <Button
          variant="contained"
          size="large"
          onClick={handleNext}
          disabled={finalizing}
          fullWidth
        >
          {finalizing && <CircularProgress size={20} sx={{ mr: 1 }} />}
          {isLastQuestion
            ? source === "today" ? "ホームに戻る" : "結果を見る"
            : "次の問題へ →"}
        </Button>
      </Box>
    </Box>
  );
}
