import Box from "@mui/material/Box";
import { CatBreedList } from "@/features/cat-breeds";

export default function CatBreedsPage() {
  return (
    <Box sx={{ px: 2, pt: 3, pb: 2 }}>
      <CatBreedList />
    </Box>
  );
}
