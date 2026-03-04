"use client";

import { useState } from "react";
import Box from "@mui/material/Box";
import IconButton from "@mui/material/IconButton";
import Typography from "@mui/material/Typography";
import ChevronLeftIcon from "@mui/icons-material/ChevronLeft";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import type { CatPhotoResponse } from "@/shared/api/generated";

interface PhotoCarouselProps {
  photos: CatPhotoResponse[];
  altText: string;
}

export function PhotoCarousel({ photos, altText }: PhotoCarouselProps) {
  const [currentIndex, setCurrentIndex] = useState(0);

  if (photos.length === 0) {
    return (
      <Box
        sx={{
          width: "100%",
          height: 300,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          bgcolor: "grey.200",
          borderRadius: 1,
        }}
      >
        <Typography color="text.secondary">{"写真がありません"}</Typography>
      </Box>
    );
  }

  const handlePrev = () => {
    setCurrentIndex((prev) => (prev > 0 ? prev - 1 : photos.length - 1));
  };

  const handleNext = () => {
    setCurrentIndex((prev) => (prev < photos.length - 1 ? prev + 1 : 0));
  };

  return (
    <Box sx={{ position: "relative", width: "100%" }}>
      <Box
        component="img"
        src={photos[currentIndex].url}
        alt={`${altText} - ${currentIndex + 1}`}
        sx={{
          width: "100%",
          height: 400,
          objectFit: "cover",
          borderRadius: 1,
        }}
      />

      {photos.length > 1 && (
        <>
          <IconButton
            onClick={handlePrev}
            aria-label="前の写真"
            sx={{
              position: "absolute",
              left: 8,
              top: "50%",
              transform: "translateY(-50%)",
              bgcolor: "rgba(255,255,255,0.8)",
              "&:hover": { bgcolor: "rgba(255,255,255,0.95)" },
            }}
          >
            <ChevronLeftIcon />
          </IconButton>
          <IconButton
            onClick={handleNext}
            aria-label="次の写真"
            sx={{
              position: "absolute",
              right: 8,
              top: "50%",
              transform: "translateY(-50%)",
              bgcolor: "rgba(255,255,255,0.8)",
              "&:hover": { bgcolor: "rgba(255,255,255,0.95)" },
            }}
          >
            <ChevronRightIcon />
          </IconButton>
        </>
      )}

      <Typography
        variant="caption"
        sx={{
          position: "absolute",
          bottom: 8,
          right: 8,
          bgcolor: "rgba(0,0,0,0.6)",
          color: "white",
          px: 1,
          py: 0.5,
          borderRadius: 1,
        }}
      >
        {`${currentIndex + 1} / ${photos.length}`}
      </Typography>
    </Box>
  );
}
