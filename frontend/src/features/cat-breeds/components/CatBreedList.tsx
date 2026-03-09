"use client";

import { useState } from "react";
import Box from "@mui/material/Box";
import CircularProgress from "@mui/material/CircularProgress";
import Grid from "@mui/material/Grid";
import Typography from "@mui/material/Typography";
import MenuBookRoundedIcon from "@mui/icons-material/MenuBookRounded";
import type { GetCatBreedsApiV1CatBreedsGetParams } from "@/shared/api/generated";
import { useCatBreeds } from "../hooks";
import { CatBreedCard } from "./CatBreedCard";
import { CatBreedFilters } from "./CatBreedFilters";

interface FilterState {
  coatColorId: string;
  coatPatternId: string;
  coatLengthId: string;
}

export function CatBreedList() {
  const [filters, setFilters] = useState<FilterState>({
    coatColorId: "",
    coatPatternId: "",
    coatLengthId: "",
  });

  const params: GetCatBreedsApiV1CatBreedsGetParams = {
    coat_color_id: filters.coatColorId || undefined,
    coat_pattern_id: filters.coatPatternId || undefined,
    coat_length_id: filters.coatLengthId || undefined,
  };

  const { data: breeds, isLoading, error } = useCatBreeds(params);

  return (
    <Box>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 3 }}>
        <MenuBookRoundedIcon sx={{ color: "primary.main", fontSize: 24 }} />
        <Typography variant="h5" component="h1" fontWeight={700}>
          {"猫図鑑"}
        </Typography>
      </Box>

      <CatBreedFilters filters={filters} onFilterChange={setFilters} />

      {isLoading && (
        <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {error && (
        <Typography color="error" sx={{ py: 2 }}>
          {"データの取得に失敗しました"}
        </Typography>
      )}

      {!isLoading && breeds && breeds.length === 0 && (
        <Typography color="text.secondary" sx={{ py: 2 }}>
          {"該当する猫種が見つかりません"}
        </Typography>
      )}

      {breeds && breeds.length > 0 && (
        <Grid container spacing={2}>
          {breeds.map((breed) => (
            <Grid item xs={12} sm={6} md={4} lg={3} key={breed.id}>
              <CatBreedCard breed={breed} />
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  );
}
