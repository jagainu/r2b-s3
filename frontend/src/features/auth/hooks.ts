/**
 * Auth feature hooks
 *
 * TanStack Query を使用した認証関連のカスタム hooks。
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback } from "react";

import {
  getMeApi,
  googleAuthApi,
  loginApi,
  logoutApi,
  registerApi,
} from "./api";
import type {
  GoogleAuthRequest,
  LoginRequest,
  RegisterRequest,
  UserResponse,
} from "./api";

// --- Query Keys ---

const AUTH_KEYS = {
  me: ["auth", "me"] as const,
};

// --- Hooks ---

/**
 * 現在のログインユーザーを取得する。
 * Cookie ベースなので、ログイン済みなら自動的にユーザー情報が返る。
 */
export function useCurrentUser() {
  return useQuery({
    queryKey: AUTH_KEYS.me,
    queryFn: async () => {
      const res = await getMeApi();
      return res.data;
    },
    retry: false,
    staleTime: 5 * 60 * 1000, // 5分
  });
}

/**
 * メール + パスワードでログインする。
 */
export function useLogin() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (body: LoginRequest) => {
      const res = await loginApi(body);
      if (res.status >= 400) {
        const errorData = res.data as unknown as { detail: string };
        throw new Error(errorData.detail || "ログインに失敗しました");
      }
      return res.data as UserResponse;
    },
    onSuccess: (user) => {
      queryClient.setQueryData(AUTH_KEYS.me, user);
    },
  });
}

/**
 * メール + パスワード + ユーザー名で新規登録する。
 */
export function useRegister() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (body: RegisterRequest) => {
      const res = await registerApi(body);
      if (res.status >= 400) {
        const errorData = res.data as unknown as { detail: string };
        throw new Error(errorData.detail || "登録に失敗しました");
      }
      return res.data as UserResponse;
    },
    onSuccess: (user) => {
      queryClient.setQueryData(AUTH_KEYS.me, user);
    },
  });
}

/**
 * Google OAuth でログイン/登録する。
 */
export function useGoogleAuth() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (body: GoogleAuthRequest) => {
      const res = await googleAuthApi(body);
      if (res.status >= 400) {
        const errorData = res.data as unknown as { detail: string };
        throw new Error(errorData.detail || "Google認証に失敗しました");
      }
      return res.data as UserResponse;
    },
    onSuccess: (user) => {
      queryClient.setQueryData(AUTH_KEYS.me, user);
    },
  });
}

/**
 * ログアウトする。
 */
export function useLogout() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      await logoutApi();
    },
    onSuccess: () => {
      queryClient.setQueryData(AUTH_KEYS.me, null);
      queryClient.clear();
    },
  });
}

/**
 * Google OAuth の認可 URL を生成して遷移する。
 */
export function useGoogleLogin() {
  const handleGoogleLogin = useCallback(() => {
    const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
    if (!clientId) {
      console.error("NEXT_PUBLIC_GOOGLE_CLIENT_ID is not configured");
      return;
    }

    const redirectUri = `${window.location.origin}/auth/callback`;
    const scope = "openid email profile";
    const responseType = "code";

    const params = new URLSearchParams({
      client_id: clientId,
      redirect_uri: redirectUri,
      scope,
      response_type: responseType,
      access_type: "offline",
      prompt: "consent",
    });

    window.location.href = `https://accounts.google.com/o/oauth2/v2/auth?${params}`;
  }, []);

  return handleGoogleLogin;
}
