"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import CardMedia from "@mui/material/CardMedia";
import CircularProgress from "@mui/material/CircularProgress";
import Typography from "@mui/material/Typography";
import type { QuizChoiceResponse } from "@/shared/api/generated";
import { useTodayQuiz, useSubmitAnswer } from "../hooks";

/** P001 ホーム画面: 今日の一匹カード */
export function TodayQuizCard() {
  const { data, isLoading, error } = useTodayQuiz();
  const [selectedChoiceId, setSelectedChoiceId] = useState<string | null>(null);
  const { mutate: submitAnswer, isPending } = useSubmitAnswer();
  const router = useRouter();

  if (isLoading) {
    return (
      <Card sx={{ maxWidth: 400 }}>
        <CardContent sx={{ display: "flex", justifyContent: "center", py: 4 }}>
          <CircularProgress />
        </CardContent>
      </Card>
    );
  }

  if (error || !data) {
    return null;
  }

  const handleChoiceClick = (choice: QuizChoiceResponse) => {
    if (selectedChoiceId || isPending) return;
    setSelectedChoiceId(choice.id);

    submitAnswer(
      {
        session_id: data.session_id,
        question_number: data.question_number ?? 1,
        selected_cat_id: choice.id,
      },
      {
        onSuccess: (result) => {
          // 解説画面へ遷移
          const params = new URLSearchParams({
            isCorrect: String(result.is_correct),
            correctCatId: result.correct_cat_id,
            sessionId: data.session_id,
            questionIndex: "0",
            totalQuestions: "1",
            source: "today",
          });
          router.push(`/quiz/explanation?${params.toString()}`);
        },
        onError: () => {
          setSelectedChoiceId(null);
        },
      },
    );
  };

  return (
    <Card sx={{ maxWidth: 400 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          {"今日の一匹"}
        </Typography>

        {/* photo_to_name: 写真を表示 */}
        {data.question_type === "photo_to_name" && data.photo_url && (
          <CardMedia
            component="img"
            height="200"
            image={data.photo_url}
            alt="今日の一匹"
            sx={{ borderRadius: 1, mb: 2, objectFit: "cover" }}
          />
        )}

        {/* name_to_photo: 猫名を表示 */}
        {data.question_type === "name_to_photo" && data.cat_name && (
          <Typography variant="h5" align="center" sx={{ py: 2 }}>
            {data.cat_name}
          </Typography>
        )}

        {/* 選択肢 */}
        <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
          {data.choices.map((choice) => {
            const isSelected = selectedChoiceId === choice.id;
            return (
              <Button
                key={choice.id}
                variant={isSelected ? "contained" : "outlined"}
                onClick={() => handleChoiceClick(choice)}
                disabled={!!selectedChoiceId || isPending}
                sx={{
                  justifyContent: "flex-start",
                  textTransform: "none",
                  p: data.question_type === "name_to_photo" ? 0 : undefined,
                  overflow: "hidden",
                }}
              >
                {isPending && isSelected && (
                  <CircularProgress size={16} sx={{ mr: 1 }} />
                )}
                {data.question_type === "photo_to_name" ? choice.name : null}
                {data.question_type === "name_to_photo" && choice.photo_url && (
                  <Box
                    component="img"
                    src={choice.photo_url}
                    alt="選択肢"
                    sx={{
                      width: "100%",
                      height: 100,
                      objectFit: "cover",
                      display: "block",
                    }}
                  />
                )}
              </Button>
            );
          })}
        </Box>
      </CardContent>
    </Card>
  );
}
