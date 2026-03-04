"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import type {
  AnswerRequest,
  AnswerResponse,
  FinalizeResponse,
  LatestSessionResponse,
  QuizSessionResponse,
  TodayQuizResponse,
  UserStatsResponse,
} from "@/shared/api/generated";
import {
  createQuizSession,
  fetchTodayQuiz,
  submitAnswer,
  finalizeSession,
  fetchUserStats,
  fetchLatestSession,
} from "./api";

/** クイズセッションを作成する mutation hook */
export function useCreateQuizSession() {
  return useMutation<QuizSessionResponse, Error>({
    mutationFn: async () => {
      const res = await createQuizSession();
      return res.data;
    },
  });
}

/** 今日の一匹クイズを取得する hook */
export function useTodayQuiz() {
  return useQuery<TodayQuizResponse>({
    queryKey: ["today-quiz"],
    queryFn: async () => {
      const res = await fetchTodayQuiz();
      return res.data;
    },
  });
}

/** クイズ回答を送信する mutation hook */
export function useSubmitAnswer() {
  return useMutation<AnswerResponse, Error, AnswerRequest>({
    mutationFn: async (body: AnswerRequest) => {
      const res = await submitAnswer(body);
      return res.data;
    },
  });
}

/** セッションを完了する mutation hook */
export function useFinalizeSession() {
  return useMutation<FinalizeResponse, Error, string>({
    mutationFn: async (sessionId: string) => {
      const res = await finalizeSession(sessionId);
      return res.data;
    },
  });
}

/** ユーザー統計（累計覚えた種類数）を取得する hook */
export function useUserStats() {
  return useQuery<UserStatsResponse>({
    queryKey: ["user-stats"],
    queryFn: async () => {
      const res = await fetchUserStats();
      return res.data;
    },
  });
}

/** 最新セッション結果を取得する hook */
export function useLatestSession(source: string) {
  return useQuery<LatestSessionResponse>({
    queryKey: ["latest-session", source],
    queryFn: async () => {
      const res = await fetchLatestSession(source);
      return res.data;
    },
  });
}
