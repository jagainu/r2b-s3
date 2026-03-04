"use client";

import Card from "@mui/material/Card";
import CardActionArea from "@mui/material/CardActionArea";
import CardContent from "@mui/material/CardContent";
import CardMedia from "@mui/material/CardMedia";
import Chip from "@mui/material/Chip";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useRouter } from "next/navigation";
import type { CatBreedListItem } from "@/shared/api/generated";

interface CatBreedCardProps {
  breed: CatBreedListItem;
}

export function CatBreedCard({ breed }: CatBreedCardProps) {
  const router = useRouter();

  const handleClick = () => {
    router.push(`/cat-breeds/${breed.id}`);
  };

  return (
    <Card sx={{ height: "100%" }}>
      <CardActionArea onClick={handleClick} data-testid={`cat-card-${breed.id}`}>
        {breed.thumbnail_url && (
          <CardMedia
            component="img"
            height="180"
            image={breed.thumbnail_url}
            alt={breed.name}
            sx={{ objectFit: "cover" }}
          />
        )}
        <CardContent>
          <Typography variant="h6" component="div" gutterBottom>
            {breed.name}
          </Typography>
          <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
            <Chip label={breed.coat_color.name} size="small" color="primary" variant="outlined" />
            <Chip label={breed.coat_pattern.name} size="small" color="secondary" variant="outlined" />
            <Chip label={breed.coat_length.name} size="small" variant="outlined" />
          </Stack>
        </CardContent>
      </CardActionArea>
    </Card>
  );
}
