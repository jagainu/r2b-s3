"use client";

import { useState } from "react";
import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Divider from "@mui/material/Divider";
import Tab from "@mui/material/Tab";
import Tabs from "@mui/material/Tabs";
import Typography from "@mui/material/Typography";
import { useRouter } from "next/navigation";

import { LoginForm } from "./LoginForm";
import { RegisterForm } from "./RegisterForm";
import { GoogleLoginButton } from "./GoogleLoginButton";

export function AuthTabs() {
  const [tabIndex, setTabIndex] = useState(0);
  const router = useRouter();

  const handleSuccess = () => {
    router.push("/dashboard");
  };

  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "100vh",
        p: 2,
      }}
    >
      <Card sx={{ maxWidth: 440, width: "100%" }}>
        <CardContent sx={{ p: 4 }}>
          <Typography
            variant="h5"
            component="h1"
            fontWeight="bold"
            mb={1}
            textAlign="center"
          >
            猫の種類学習アプリ
          </Typography>

          <Tabs
            value={tabIndex}
            onChange={(_, newValue) => setTabIndex(newValue)}
            variant="fullWidth"
            sx={{ mb: 2 }}
          >
            <Tab label="ログイン" />
            <Tab label="新規登録" />
          </Tabs>

          {tabIndex === 0 ? (
            <LoginForm onSuccess={handleSuccess} />
          ) : (
            <RegisterForm onSuccess={handleSuccess} />
          )}

          <Divider sx={{ my: 2 }}>または</Divider>

          <GoogleLoginButton />
        </CardContent>
      </Card>
    </Box>
  );
}
