"use client";

import { useState } from "react";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import TextField from "@mui/material/TextField";
import CircularProgress from "@mui/material/CircularProgress";

import { useLogin } from "../hooks";

interface LoginFormProps {
  onSuccess: () => void;
}

export function LoginForm({ onSuccess }: LoginFormProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [validationErrors, setValidationErrors] = useState<{
    email?: string;
    password?: string;
  }>({});

  const loginMutation = useLogin();

  const validate = (): boolean => {
    const errors: { email?: string; password?: string } = {};

    if (!email.trim()) {
      errors.email = "メールアドレスを入力してください";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      errors.email = "有効なメールアドレスを入力してください";
    }

    if (!password) {
      errors.password = "パスワードを入力してください";
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    loginMutation.mutate(
      { email, password },
      { onSuccess },
    );
  };

  return (
    <Box component="form" onSubmit={handleSubmit} noValidate>
      {loginMutation.error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {loginMutation.error.message}
        </Alert>
      )}

      <TextField
        label="メールアドレス"
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        error={!!validationErrors.email}
        helperText={validationErrors.email}
        fullWidth
        margin="normal"
        autoComplete="email"
        autoFocus
      />

      <TextField
        label="パスワード"
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        error={!!validationErrors.password}
        helperText={validationErrors.password}
        fullWidth
        margin="normal"
        autoComplete="current-password"
      />

      <Button
        type="submit"
        variant="contained"
        fullWidth
        size="large"
        disabled={loginMutation.isPending}
        sx={{ mt: 2, mb: 1 }}
      >
        {loginMutation.isPending ? (
          <CircularProgress size={24} color="inherit" />
        ) : (
          "ログイン"
        )}
      </Button>
    </Box>
  );
}
