"use client";

import { useState } from "react";
import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Divider from "@mui/material/Divider";
import Tab from "@mui/material/Tab";
import Tabs from "@mui/material/Tabs";
import Typography from "@mui/material/Typography";
import PetsIcon from "@mui/icons-material/Pets";
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
        background: "linear-gradient(160deg, #FAF5EE 0%, #F0E6D8 50%, #FAF5EE 100%)",
        position: "relative",
        overflow: "hidden",
        "&::before": {
          content: '""',
          position: "absolute",
          top: -120,
          right: -120,
          width: 400,
          height: 400,
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(196,87,10,0.08) 0%, transparent 70%)",
          pointerEvents: "none",
        },
        "&::after": {
          content: '""',
          position: "absolute",
          bottom: -80,
          left: -80,
          width: 300,
          height: 300,
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(107,124,94,0.08) 0%, transparent 70%)",
          pointerEvents: "none",
        },
      }}
    >
      <Card
        sx={{
          maxWidth: 420,
          width: "100%",
          position: "relative",
          zIndex: 1,
          borderRadius: 4,
        }}
      >
        <CardContent sx={{ p: { xs: 3, sm: 4 } }}>
          {/* ロゴ */}
          <Box sx={{ textAlign: "center", mb: 3 }}>
            <Box
              sx={{
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                width: 56,
                height: 56,
                borderRadius: "50%",
                background: "linear-gradient(135deg, #C4570A 0%, #E8835A 100%)",
                mb: 1.5,
                boxShadow: "0 4px 16px rgba(196, 87, 10, 0.3)",
              }}
            >
              <PetsIcon sx={{ color: "#FFFFFF", fontSize: 28 }} />
            </Box>
            <Typography
              variant="h5"
              component="h1"
              fontWeight={700}
              sx={{ color: "text.primary", letterSpacing: "-0.01em" }}
            >
              猫の種類学習
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
              猫の種類を楽しく覚えよう
            </Typography>
          </Box>

          <Tabs
            value={tabIndex}
            onChange={(_, v) => setTabIndex(v)}
            variant="fullWidth"
            sx={{
              mb: 2,
              "& .MuiTabs-indicator": {
                height: 3,
                borderRadius: 2,
                background: "linear-gradient(90deg, #C4570A 0%, #E8835A 100%)",
              },
              "& .MuiTab-root": {
                fontWeight: 600,
                fontSize: "0.95rem",
              },
            }}
          >
            <Tab label="ログイン" />
            <Tab label="新規登録" />
          </Tabs>

          {tabIndex === 0 ? (
            <LoginForm onSuccess={handleSuccess} />
          ) : (
            <RegisterForm onSuccess={handleSuccess} />
          )}

          <Divider sx={{ my: 2.5, fontSize: "0.8rem" }}>または</Divider>

          <GoogleLoginButton />
        </CardContent>
      </Card>
    </Box>
  );
}
