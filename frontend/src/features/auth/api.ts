/**
 * Auth feature API layer
 *
 * orval 生成コードを customInstance mutator 経由でラップする。
 * 直接 orval 生成関数を使うのではなく、customInstance を経由して
 * Cookie 認証・CSRF 自動付与・トークン自動更新を適用する。
 */
import { customInstance } from "@/shared/api/mutator";
import type {
  GoogleAuthRequest,
  LoginRequest,
  RegisterRequest,
  UserResponse,
} from "@/shared/api/generated";

// --- 型定義 ---

interface ApiResponse<T> {
  data: T;
  status: number;
  headers: Headers;
}

interface ApiError {
  detail: string;
}

// --- API 関数 ---

export async function loginApi(
  body: LoginRequest,
): Promise<ApiResponse<UserResponse>> {
  return customInstance<ApiResponse<UserResponse>>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function registerApi(
  body: RegisterRequest,
): Promise<ApiResponse<UserResponse>> {
  return customInstance<ApiResponse<UserResponse>>("/api/v1/auth/register", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function googleAuthApi(
  body: GoogleAuthRequest,
): Promise<ApiResponse<UserResponse>> {
  return customInstance<ApiResponse<UserResponse>>("/api/v1/auth/google", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function logoutApi(): Promise<ApiResponse<void>> {
  return customInstance<ApiResponse<void>>("/api/v1/auth/logout", {
    method: "POST",
  });
}

export async function getMeApi(): Promise<ApiResponse<UserResponse>> {
  return customInstance<ApiResponse<UserResponse>>("/api/v1/auth/me", {
    method: "GET",
  });
}

export type { ApiResponse, ApiError, UserResponse, LoginRequest, RegisterRequest, GoogleAuthRequest };
