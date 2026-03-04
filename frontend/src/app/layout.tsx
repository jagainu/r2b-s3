import type { Metadata } from "next";
import { Providers } from "@/shared/ui/Providers";

export const metadata: Metadata = {
  title: "猫の種類学習アプリ",
  description: "猫の種類を楽しく覚えよう",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ja">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
