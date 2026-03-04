"use client";

import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import CardActionArea from "@mui/material/CardActionArea";
import CardContent from "@mui/material/CardContent";
import CardMedia from "@mui/material/CardMedia";
import CircularProgress from "@mui/material/CircularProgress";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useRouter } from "next/navigation";
import { useSimilarCats } from "../hooks";

interface SimilarCatsProps {
  breedId: string;
}

export function SimilarCats({ breedId }: SimilarCatsProps) {
  const router = useRouter();
  const { data: similarCats, isLoading } = useSimilarCats(breedId);

  if (isLoading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 2 }}>
        <CircularProgress size={24} />
      </Box>
    );
  }

  if (!similarCats || similarCats.length === 0) {
    return null;
  }

  return (
    <Box sx={{ mt: 3 }}>
      <Typography variant="h6" gutterBottom>
        {"似ている猫種"}
      </Typography>
      <Stack direction="row" spacing={2} sx={{ overflowX: "auto" }}>
        {similarCats.map((cat) => (
          <Card key={cat.id} sx={{ minWidth: 160, flexShrink: 0 }}>
            <CardActionArea onClick={() => router.push(`/cat-breeds/${cat.id}`)}>
              {cat.thumbnail_url && (
                <CardMedia
                  component="img"
                  height="120"
                  image={cat.thumbnail_url}
                  alt={cat.name}
                  sx={{ objectFit: "cover" }}
                />
              )}
              <CardContent sx={{ p: 1.5 }}>
                <Typography variant="body2" fontWeight="bold" noWrap>
                  {cat.name}
                </Typography>
              </CardContent>
            </CardActionArea>
          </Card>
        ))}
      </Stack>
    </Box>
  );
}
