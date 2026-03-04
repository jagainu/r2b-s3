import Box from "@mui/material/Box";
import { CatBreedList } from "@/features/cat-breeds";

export default function CatBreedsPage() {
  return (
    <Box sx={{ p: 4 }}>
      <CatBreedList />
    </Box>
  );
}
