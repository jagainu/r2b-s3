import type { NextConfig } from "next";

// 本番/stg では空文字 → Next.js がサーバーサイドでプロキシ（Mixed Content 回避）
// ローカルでは http://localhost:8000 を指定
const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

const nextConfig: NextConfig = {
  // React の strict mode を有効化（開発時の問題検出）
  reactStrictMode: true,

  // バックエンドへのリクエストを Next.js サーバー経由でプロキシ
  // NEXT_PUBLIC_API_BASE_URL が空の場合のみ有効（Vercel デプロイ時）
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${API_BASE_URL}/api/:path*`,
      },
      {
        source: "/static/:path*",
        destination: `${API_BASE_URL}/static/:path*`,
      },
    ];
  },

  // セキュリティヘッダー
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "X-XSS-Protection", value: "1; mode=block" },
        ],
      },
    ];
  },
};

export default nextConfig;
