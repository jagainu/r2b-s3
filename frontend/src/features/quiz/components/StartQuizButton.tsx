"use client";

import { useRouter } from "next/navigation";
import Button from "@mui/material/Button";
import CircularProgress from "@mui/material/CircularProgress";
import { useCreateQuizSession } from "../hooks";

/** P001 ホーム画面: 「クイズを始める」ボタン */
export function StartQuizButton() {
  const router = useRouter();
  const { mutate, isPending } = useCreateQuizSession();

  const handleClick = () => {
    mutate(undefined, {
      onSuccess: (data) => {
        // session_id をクエリパラメータで渡してクイズ画面へ遷移
        router.push(`/quiz?sessionId=${data.session_id}`);
      },
    });
  };

  return (
    <Button
      variant="contained"
      size="large"
      onClick={handleClick}
      disabled={isPending}
      sx={{ minWidth: 200, py: 1.5 }}
    >
      {isPending ? <CircularProgress size={24} /> : "クイズを始める"}
    </Button>
  );
}
