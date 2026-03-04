"use client";

import { Suspense, useEffect, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Box from "@mui/material/Box";
import CircularProgress from "@mui/material/CircularProgress";
import Typography from "@mui/material/Typography";
import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";

import { useGoogleAuth } from "@/features/auth";

function GoogleCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const googleAuthMutation = useGoogleAuth();
  const hasProcessed = useRef(false);

  useEffect(() => {
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const code = searchParams.get("code");
    const error = searchParams.get("error");

    if (error || !code) return;

    const redirectUri = `${window.location.origin}/auth/callback`;

    googleAuthMutation.mutate(
      { code, redirect_uri: redirectUri },
      {
        onSuccess: () => {
          router.push("/dashboard");
        },
      },
    );
  }, [searchParams, googleAuthMutation, router]);

  const errorFromGoogle = searchParams.get("error");

  if (errorFromGoogle) {
    return (
      <Box sx={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "100vh", p: 2 }}>
        <Box textAlign="center">
          <Alert severity="error" sx={{ mb: 2 }}>
            Google 認証がキャンセルされました
          </Alert>
          <Button variant="contained" onClick={() => router.push("/login")}>
            ログイン画面に戻る
          </Button>
        </Box>
      </Box>
    );
  }

  if (googleAuthMutation.error) {
    return (
      <Box sx={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "100vh", p: 2 }}>
        <Box textAlign="center">
          <Alert severity="error" sx={{ mb: 2 }}>
            {googleAuthMutation.error.message}
          </Alert>
          <Button variant="contained" onClick={() => router.push("/login")}>
            ログイン画面に戻る
          </Button>
        </Box>
      </Box>
    );
  }

  return (
    <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "100vh", gap: 2 }}>
      <CircularProgress />
      <Typography color="text.secondary">Google 認証を処理しています...</Typography>
    </Box>
  );
}

export default function GoogleCallbackPage() {
  return (
    <Suspense fallback={
      <Box sx={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "100vh" }}>
        <CircularProgress />
      </Box>
    }>
      <GoogleCallbackContent />
    </Suspense>
  );
}
