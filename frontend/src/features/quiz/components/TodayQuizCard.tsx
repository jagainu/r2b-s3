"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import ButtonBase from "@mui/material/ButtonBase";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import CardMedia from "@mui/material/CardMedia";
import CircularProgress from "@mui/material/CircularProgress";
import Grid from "@mui/material/Grid";
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
      <Card>
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

  const isPhotoChoice = data.question_type === "name_to_photo";

  return (
    <Card>
      <CardContent sx={{ p: 2.5 }}>
        <Typography variant="overline" color="primary" fontWeight={700} sx={{ letterSpacing: 2 }}>
          今日の一匹
        </Typography>

        {/* photo_to_name: 写真を表示 */}
        {data.question_type === "photo_to_name" && data.photo_url && (
          <CardMedia
            component="img"
            height="180"
            image={data.photo_url}
            alt="今日の一匹"
            sx={{ borderRadius: 2, my: 1.5, objectFit: "cover" }}
          />
        )}

        {/* name_to_photo: 猫名を表示 */}
        {data.question_type === "name_to_photo" && data.cat_name && (
          <Typography variant="h4" align="center" fontWeight={700} sx={{ py: 2 }}>
            {data.cat_name}
          </Typography>
        )}

        <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
          どれでしょう？
        </Typography>

        {/* name_to_photo: 2×2 画像グリッド */}
        {isPhotoChoice ? (
          <Grid container spacing={1}>
            {data.choices.map((choice) => {
              const isSelected = selectedChoiceId === choice.id;
              return (
                <Grid item xs={6} key={choice.id}>
                  <ButtonBase
                    onClick={() => handleChoiceClick(choice)}
                    disabled={!!selectedChoiceId || isPending}
                    sx={{
                      width: "100%",
                      borderRadius: 2,
                      overflow: "hidden",
                      border: "2.5px solid",
                      borderColor: isSelected ? "primary.main" : "rgba(44,35,24,0.1)",
                      transition: "border-color 0.15s",
                      display: "block",
                      "&:hover:not(:disabled)": {
                        borderColor: "primary.light",
                      },
                    }}
                  >
                    {choice.photo_url && (
                      <Box
                        component="img"
                        src={choice.photo_url}
                        alt="選択肢"
                        sx={{
                          width: "100%",
                          aspectRatio: "1",
                          objectFit: "cover",
                          display: "block",
                        }}
                      />
                    )}
                    {isPending && isSelected && (
                      <Box
                        sx={{
                          position: "absolute",
                          inset: 0,
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          bgcolor: "rgba(255,255,255,0.6)",
                        }}
                      >
                        <CircularProgress size={24} />
                      </Box>
                    )}
                  </ButtonBase>
                </Grid>
              );
            })}
          </Grid>
        ) : (
          /* photo_to_name: テキスト選択肢 */
          <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
            {data.choices.map((choice) => {
              const isSelected = selectedChoiceId === choice.id;
              return (
                <Button
                  key={choice.id}
                  variant={isSelected ? "contained" : "outlined"}
                  onClick={() => handleChoiceClick(choice)}
                  disabled={!!selectedChoiceId || isPending}
                  sx={{ justifyContent: "flex-start", textTransform: "none", py: 1.2 }}
                >
                  {isPending && isSelected && <CircularProgress size={16} sx={{ mr: 1 }} />}
                  {choice.name}
                </Button>
              );
            })}
          </Box>
        )}
      </CardContent>
    </Card>
  );
}
