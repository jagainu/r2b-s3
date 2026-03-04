import Box from "@mui/material/Box";
import { CatBreedDetail } from "@/features/cat-breeds";

interface CatBreedDetailPageProps {
  params: Promise<{ id: string }>;
}

export default async function CatBreedDetailPage({
  params,
}: CatBreedDetailPageProps) {
  const { id } = await params;
  return (
    <Box sx={{ p: 4, maxWidth: 800, mx: "auto" }}>
      <CatBreedDetail breedId={id} />
    </Box>
  );
}
