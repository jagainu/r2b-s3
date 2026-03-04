import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

export default function DashboardPage() {
  return (
    <Box sx={{ p: 4 }}>
      <Typography variant="h4" component="h1" fontWeight="bold" mb={2}>
        ダッシュボード
      </Typography>
      <Typography color="text.secondary">
        ダッシュボードは Slice 1 以降で実装されます
      </Typography>
    </Box>
  );
}
