"use client";

import { usePathname, useRouter } from "next/navigation";
import Box from "@mui/material/Box";
import BottomNavigation from "@mui/material/BottomNavigation";
import BottomNavigationAction from "@mui/material/BottomNavigationAction";
import HomeRoundedIcon from "@mui/icons-material/HomeRounded";
import MenuBookRoundedIcon from "@mui/icons-material/MenuBookRounded";

export default function PortalLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();

  const navValue = pathname.startsWith("/cat-breeds") ? 1 : 0;

  return (
    <Box
      sx={{
        minHeight: "100vh",
        bgcolor: "background.default",
        pb: "72px",
      }}
    >
      {children}
      <BottomNavigation
        value={navValue}
        onChange={(_, newValue) => {
          router.push(newValue === 0 ? "/dashboard" : "/cat-breeds");
        }}
        sx={{
          position: "fixed",
          bottom: 0,
          left: 0,
          right: 0,
          zIndex: 100,
          height: 64,
        }}
      >
        <BottomNavigationAction
          label="ホーム"
          icon={<HomeRoundedIcon />}
        />
        <BottomNavigationAction
          label="図鑑"
          icon={<MenuBookRoundedIcon />}
        />
      </BottomNavigation>
    </Box>
  );
}
