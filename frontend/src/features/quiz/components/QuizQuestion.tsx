"use client";

import { useState } from "react";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import CardMedia from "@mui/material/CardMedia";
import CircularProgress from "@mui/material/CircularProgress";
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
          // エラー時は選択状態をリセット
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
          height="250"
          image={question.photo_url}
          alt={`問題 ${question.question_number}`}
          sx={{ borderRadius: 2, mb: 3, objectFit: "cover" }}
        />
      )}

      {/* name_to_photo: 種類名を表示して写真を選ぶ */}
      {question.question_type === "name_to_photo" && question.cat_name && (
        <Typography variant="h4" align="center" sx={{ py: 3 }}>
          {question.cat_name}
        </Typography>
      )}

      {/* 選択肢 */}
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
                py: question.question_type === "name_to_photo" ? 0 : 1.5,
                px: question.question_type === "name_to_photo" ? 0 : undefined,
                overflow: "hidden",
              }}
            >
              {isPending && isSelected && (
                <CircularProgress size={16} sx={{ mr: 1 }} />
              )}
              {question.question_type === "photo_to_name" && choice.name}
              {question.question_type === "name_to_photo" &&
                choice.photo_url && (
                  <Box
                    component="img"
                    src={choice.photo_url}
                    alt="選択肢"
                    sx={{
                      width: "100%",
                      height: 120,
                      objectFit: "cover",
                      display: "block",
                    }}
                  />
                )}
            </Button>
          );
        })}
      </Box>
    </Box>
  );
}
