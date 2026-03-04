/**
 * quiz feature の API ラッパー
 *
 * orval 生成関数を wrap し、customInstance (mutator) 経由で呼び出す。
 * Cookie 認証・CSRF は mutator が自動処理する。
 */

import { customInstance } from "@/shared/api/mutator";
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
  getCreateQuizSessionApiV1QuizSessionsPostUrl,
  getGetTodayQuizApiV1QuizTodayGetUrl,
  getSubmitAnswerApiV1QuizAnswerPostUrl,
  getFinalizeSessionApiV1QuizSessionsSessionIdFinalizePostUrl,
  getGetUserStatsApiV1UsersMeStatsGetUrl,
  getGetLatestSessionApiV1UsersMeSessionsLatestGetUrl,
} from "@/shared/api/generated";

// 共通レスポンス型
interface ApiResponse<T> {
  data: T;
  status: number;
  headers: Headers;
}

/** クイズセッションを作成する（10問一括生成） */
export const createQuizSession = (): Promise<
  ApiResponse<QuizSessionResponse>
> => {
  return customInstance<ApiResponse<QuizSessionResponse>>(
    getCreateQuizSessionApiV1QuizSessionsPostUrl(),
    { method: "POST" },
  );
};

/** 今日の一匹クイズを取得する */
export const fetchTodayQuiz = (): Promise<ApiResponse<TodayQuizResponse>> => {
  return customInstance<ApiResponse<TodayQuizResponse>>(
    getGetTodayQuizApiV1QuizTodayGetUrl(),
  );
};

/** クイズ回答を送信する */
export const submitAnswer = (
  body: AnswerRequest,
): Promise<ApiResponse<AnswerResponse>> => {
  return customInstance<ApiResponse<AnswerResponse>>(
    getSubmitAnswerApiV1QuizAnswerPostUrl(),
    {
      method: "POST",
      body: JSON.stringify(body),
    },
  );
};

/** セッションを完了する */
export const finalizeSession = (
  sessionId: string,
): Promise<ApiResponse<FinalizeResponse>> => {
  return customInstance<ApiResponse<FinalizeResponse>>(
    getFinalizeSessionApiV1QuizSessionsSessionIdFinalizePostUrl(sessionId),
    { method: "POST" },
  );
};

/** ユーザー統計（累計覚えた種類数）を取得する */
export const fetchUserStats = (): Promise<ApiResponse<UserStatsResponse>> => {
  return customInstance<ApiResponse<UserStatsResponse>>(
    getGetUserStatsApiV1UsersMeStatsGetUrl(),
  );
};

/** 最新セッション結果を取得する */
export const fetchLatestSession = (
  source: string,
): Promise<ApiResponse<LatestSessionResponse>> => {
  return customInstance<ApiResponse<LatestSessionResponse>>(
    getGetLatestSessionApiV1UsersMeSessionsLatestGetUrl({ source }),
  );
};
