"use client";

import Button from "@mui/material/Button";
import GoogleIcon from "@mui/icons-material/Google";

import { useGoogleLogin } from "../hooks";

export function GoogleLoginButton() {
  const handleGoogleLogin = useGoogleLogin();

  return (
    <Button
      variant="outlined"
      fullWidth
      size="large"
      startIcon={<GoogleIcon />}
      onClick={handleGoogleLogin}
      sx={{ mt: 1 }}
    >
      Google でログイン
    </Button>
  );
}
