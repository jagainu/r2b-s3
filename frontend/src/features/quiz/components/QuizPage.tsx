"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Box from "@mui/material/Box";
import CircularProgress from "@mui/material/CircularProgress";
import Typography from "@mui/material/Typography";
import type { QuizSessionResponse } from "@/shared/api/generated";
import { useCreateQuizSession } from "../hooks";
import { QuizProgress } from "./QuizProgress";
import { QuizQuestion } from "./QuizQuestion";

/**
 * P002 クイズ画面の Client Component
 *
 * セッションデータをローカル state で管理し、1問ずつ表示する。
 * 回答送信後、解説画面へ遷移する。
 */
export function QuizPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const sessionId = searchParams.get("sessionId");
  const [sessionData, setSessionData] = useState<QuizSessionResponse | null>(
    null,
  );
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const { mutate, isPending } = useCreateQuizSession();

  // セッションデータの取得: sessionStorage キャッシュ or 新規作成
  useEffect(() => {
    if (sessionData || isPending) return;

    if (sessionId) {
      // sessionStorage からキャッシュ済みデータを復元
      const cached = sessionStorage.getItem(`quiz-session-${sessionId}`);
      if (cached) {
        setSessionData(JSON.parse(cached));
      }
      // キャッシュがない場合は新規セッションを作成
      else {
        mutate(undefined, {
          onSuccess: (data) => {
            sessionStorage.setItem(`quiz-session-${data.session_id}`, JSON.stringify(data));
            setSessionData(data);
          },
        });
      }
    } else {
      // sessionId なし: 新規セッションを作成
      mutate(undefined, {
        onSuccess: (data) => {
          sessionStorage.setItem(`quiz-session-${data.session_id}`, JSON.stringify(data));
          setSessionData(data);
        },
      });
    }
  }, [sessionId, sessionData, isPending, mutate]);

  // URL の questionIndex パラメータからインデックスを復元
  useEffect(() => {
    const indexParam = searchParams.get("questionIndex");
    if (indexParam !== null) {
      const idx = parseInt(indexParam, 10);
      if (!isNaN(idx) && idx >= 0) {
        setCurrentQuestionIndex(idx);
      }
    }
  }, [searchParams]);

  if (isPending || (!sessionData && !sessionId)) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!sessionData) {
    return (
      <Typography color="error" sx={{ py: 4 }}>
        {"クイズデータの取得に失敗しました"}
      </Typography>
    );
  }

  const currentQuestion = sessionData.questions[currentQuestionIndex];
  if (!currentQuestion) {
    return (
      <Typography sx={{ py: 4 }}>
        {"全ての問題に回答しました。結果画面は Slice 5 で実装されます。"}
      </Typography>
    );
  }

  const handleAnswered = (isCorrect: boolean, correctCatId: string) => {
    // 解説画面へ遷移（正誤フラグ、正解猫ID、セッション情報を渡す）
    const params = new URLSearchParams({
      isCorrect: String(isCorrect),
      correctCatId,
      sessionId: sessionData.session_id,
      questionIndex: String(currentQuestionIndex),
      totalQuestions: String(sessionData.questions.length),
    });
    router.push(`/quiz/explanation?${params.toString()}`);
  };

  return (
    <Box>
      <QuizProgress
        currentQuestion={currentQuestionIndex + 1}
        totalQuestions={sessionData.questions.length}
      />
      <QuizQuestion
        key={currentQuestion.question_number}
        question={currentQuestion}
        sessionId={sessionData.session_id}
        onAnswered={handleAnswered}
      />
    </Box>
  );
}
