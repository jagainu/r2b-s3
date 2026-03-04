"use client";

import { useState } from "react";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import TextField from "@mui/material/TextField";
import CircularProgress from "@mui/material/CircularProgress";

import { useRegister } from "../hooks";

interface RegisterFormProps {
  onSuccess: () => void;
}

export function RegisterForm({ onSuccess }: RegisterFormProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [username, setUsername] = useState("");
  const [validationErrors, setValidationErrors] = useState<{
    email?: string;
    password?: string;
    username?: string;
  }>({});

  const registerMutation = useRegister();

  const validate = (): boolean => {
    const errors: { email?: string; password?: string; username?: string } = {};

    if (!email.trim()) {
      errors.email = "メールアドレスを入力してください";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      errors.email = "有効なメールアドレスを入力してください";
    }

    if (!password) {
      errors.password = "パスワードを入力してください";
    } else if (password.length < 8) {
      errors.password = "パスワードは8文字以上で入力してください";
    }

    if (!username.trim()) {
      errors.username = "ユーザー名を入力してください";
    } else if (username.trim().length < 2) {
      errors.username = "ユーザー名は2文字以上で入力してください";
    } else if (username.trim().length > 20) {
      errors.username = "ユーザー名は20文字以内で入力してください";
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    registerMutation.mutate(
      { email, password, username: username.trim() },
      { onSuccess },
    );
  };

  return (
    <Box component="form" onSubmit={handleSubmit} noValidate>
      {registerMutation.error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {registerMutation.error.message}
        </Alert>
      )}

      <TextField
        label="ユーザー名"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        error={!!validationErrors.username}
        helperText={validationErrors.username}
        fullWidth
        margin="normal"
        autoComplete="username"
        autoFocus
        inputProps={{ minLength: 2, maxLength: 20 }}
      />

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
      />

      <TextField
        label="パスワード"
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        error={!!validationErrors.password}
        helperText={validationErrors.password || "8文字以上"}
        fullWidth
        margin="normal"
        autoComplete="new-password"
      />

      <Button
        type="submit"
        variant="contained"
        fullWidth
        size="large"
        disabled={registerMutation.isPending}
        sx={{ mt: 2, mb: 1 }}
      >
        {registerMutation.isPending ? (
          <CircularProgress size={24} color="inherit" />
        ) : (
          "新規登録"
        )}
      </Button>
    </Box>
  );
}
