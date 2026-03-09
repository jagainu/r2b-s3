"use client";

import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import CardActionArea from "@mui/material/CardActionArea";
import CardMedia from "@mui/material/CardMedia";
import Chip from "@mui/material/Chip";
import Typography from "@mui/material/Typography";
import { useRouter } from "next/navigation";
import type { CatBreedListItem } from "@/shared/api/generated";

interface CatBreedCardProps {
  breed: CatBreedListItem;
}

export function CatBreedCard({ breed }: CatBreedCardProps) {
  const router = useRouter();

  return (
    <Card sx={{ height: "100%", overflow: "hidden" }}>
      <CardActionArea
        onClick={() => router.push(`/cat-breeds/${breed.id}`)}
        data-testid={`cat-card-${breed.id}`}
        sx={{ height: "100%", display: "flex", flexDirection: "column", alignItems: "stretch" }}
      >
        {breed.thumbnail_url && (
          <CardMedia
            component="img"
            height="160"
            image={breed.thumbnail_url}
            alt={breed.name}
            sx={{ objectFit: "cover" }}
          />
        )}
        <Box sx={{ p: 1.5, flexGrow: 1 }}>
          <Typography variant="subtitle1" fontWeight={700} gutterBottom sx={{ lineHeight: 1.3 }}>
            {breed.name}
          </Typography>
          <Box sx={{ display: "flex", gap: 0.5, flexWrap: "wrap" }}>
            <Chip label={breed.coat_color.name} size="small" color="primary" variant="outlined" />
            <Chip label={breed.coat_length.name} size="small" variant="outlined" />
          </Box>
        </Box>
      </CardActionArea>
    </Card>
  );
}
