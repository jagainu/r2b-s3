import type { NextConfig } from "next";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

const nextConfig: NextConfig = {
  // React の strict mode を有効化（開発時の問題検出）
  reactStrictMode: true,

  // バックエンドの静的ファイル（猫画像）を Next.js 経由でプロキシ
  async rewrites() {
    return [
      {
        source: "/static/:path*",
        destination: `${API_BASE_URL}/static/:path*`,
      },
    ];
  },

  // CORS 対応: クロスオリジン Cookie のため credentials を許可
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
