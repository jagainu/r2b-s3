import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // React の strict mode を有効化（開発時の問題検出）
  reactStrictMode: true,

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
