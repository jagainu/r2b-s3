import type { NextConfig } from "next";

// BACKEND_URL: サーバーサイドリライト先（next.config.ts 用）
// ローカル: http://localhost:8000 / Vercel: ALB エンドポイント
const BACKEND_URL =
  process.env.BACKEND_URL || "http://localhost:8000";

const nextConfig: NextConfig = {
  // React の strict mode を有効化（開発時の問題検出）
  reactStrictMode: true,

  // バックエンドへのリクエストを Next.js サーバー経由でプロキシ
  // ブラウザは /api/* → Next.js server → BACKEND_URL へ転送
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${BACKEND_URL}/api/:path*`,
      },
      {
        source: "/static/:path*",
        destination: `${BACKEND_URL}/static/:path*`,
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
