"use client";

import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { useRouter } from "next/navigation";
import { useCatBreedDetail } from "../hooks";
import { PhotoCarousel } from "./PhotoCarousel";
import { SimilarCats } from "./SimilarCats";

interface CatBreedDetailProps {
  breedId: string;
}

export function CatBreedDetail({ breedId }: CatBreedDetailProps) {
  const router = useRouter();
  const { data: breed, isLoading, error } = useCatBreedDetail(breedId);

  if (isLoading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error || !breed) {
    return (
      <Box sx={{ py: 4 }}>
        <Typography color="error">{"猫種が見つかりません"}</Typography>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => router.push("/cat-breeds")}
          sx={{ mt: 2 }}
        >
          {"図鑑に戻る"}
        </Button>
      </Box>
    );
  }

  return (
    <Box>
      <Button
        startIcon={<ArrowBackIcon />}
        onClick={() => router.push("/cat-breeds")}
        sx={{ mb: 2 }}
      >
        {"図鑑に戻る"}
      </Button>

      <PhotoCarousel photos={breed.photos} altText={breed.name} />

      <Typography variant="h4" component="h1" fontWeight="bold" mt={3} mb={2}>
        {breed.name}
      </Typography>

      <Typography variant="h6" gutterBottom>
        {"特徴"}
      </Typography>
      <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap sx={{ mb: 2 }}>
        <Chip
          label={`毛色: ${breed.coat_color.name}`}
          color="primary"
          variant="outlined"
        />
        <Chip
          label={`模様: ${breed.coat_pattern.name}`}
          color="secondary"
          variant="outlined"
        />
        <Chip
          label={`毛の長さ: ${breed.coat_length.name}`}
          variant="outlined"
        />
      </Stack>

      <SimilarCats breedId={breedId} />
    </Box>
  );
}
