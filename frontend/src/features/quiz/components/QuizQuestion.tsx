"use client";

import { useState } from "react";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import ButtonBase from "@mui/material/ButtonBase";
import CardMedia from "@mui/material/CardMedia";
import CircularProgress from "@mui/material/CircularProgress";
import Grid from "@mui/material/Grid";
import Typography from "@mui/material/Typography";
import type {
  QuizChoiceResponse,
  QuizQuestionResponse,
} from "@/shared/api/generated";
import { useSubmitAnswer } from "../hooks";

interface QuizQuestionProps {
  question: QuizQuestionResponse;
  sessionId: string;
  onAnswered?: (isCorrect: boolean, correctCatId: string) => void;
}

/** P002 クイズ画面: 1問分の問題表示・選択肢 */
export function QuizQuestion({
  question,
  sessionId,
  onAnswered,
}: QuizQuestionProps) {
  const [selectedChoiceId, setSelectedChoiceId] = useState<string | null>(null);
  const { mutate: submitAnswer, isPending } = useSubmitAnswer();

  const handleChoiceClick = (choice: QuizChoiceResponse) => {
    if (selectedChoiceId || isPending) return;
    setSelectedChoiceId(choice.id);

    submitAnswer(
      {
        session_id: sessionId,
        question_number: question.question_number,
        selected_cat_id: choice.id,
      },
      {
        onSuccess: (data) => {
          onAnswered?.(data.is_correct, data.correct_cat_id);
        },
        onError: () => {
          setSelectedChoiceId(null);
        },
      },
    );
  };

  return (
    <Box>
      {/* photo_to_name: 写真を表示して種類名を選ぶ */}
      {question.question_type === "photo_to_name" && question.photo_url && (
        <CardMedia
          component="img"
          height="260"
          image={question.photo_url}
          alt={`問題 ${question.question_number}`}
          sx={{ borderRadius: 3, mb: 3, objectFit: "cover" }}
        />
      )}

      {/* name_to_photo: 種類名を表示して写真を選ぶ */}
      {question.question_type === "name_to_photo" && question.cat_name && (
        <Box sx={{ textAlign: "center", py: 2, mb: 1 }}>
          <Typography variant="overline" color="text.secondary" sx={{ letterSpacing: 2 }}>
            この猫はどれ？
          </Typography>
          <Typography variant="h3" fontWeight={700} sx={{ mt: 0.5 }}>
            {question.cat_name}
          </Typography>
        </Box>
      )}

      {/* name_to_photo: 2×2 画像グリッド */}
      {question.question_type === "name_to_photo" ? (
        <Grid container spacing={1.5}>
          {question.choices.map((choice) => {
            const isSelected = selectedChoiceId === choice.id;
            return (
              <Grid item xs={6} key={choice.id}>
                <ButtonBase
                  onClick={() => handleChoiceClick(choice)}
                  disabled={!!selectedChoiceId || isPending}
                  sx={{
                    width: "100%",
                    borderRadius: 2.5,
                    overflow: "hidden",
                    border: "3px solid",
                    borderColor: isSelected ? "primary.main" : "rgba(44,35,24,0.1)",
                    transition: "border-color 0.15s, transform 0.1s",
                    display: "block",
                    position: "relative",
                    "&:hover:not(:disabled)": {
                      borderColor: "primary.light",
                      transform: "scale(1.02)",
                    },
                    "&:active:not(:disabled)": {
                      transform: "scale(0.98)",
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
                        bgcolor: "rgba(255,255,255,0.7)",
                      }}
                    >
                      <CircularProgress size={28} />
                    </Box>
                  )}
                </ButtonBase>
              </Grid>
            );
          })}
        </Grid>
      ) : (
        /* photo_to_name: テキスト選択肢 */
        <Box sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
          {question.choices.map((choice) => {
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
                  py: 1.5,
                  fontSize: "1rem",
                }}
              >
                {isPending && isSelected && (
                  <CircularProgress size={16} sx={{ mr: 1 }} />
                )}
                {choice.name}
              </Button>
            );
          })}
        </Box>
      )}
    </Box>
  );
}
