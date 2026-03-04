"use client";

import Box from "@mui/material/Box";
import FormControl from "@mui/material/FormControl";
import InputLabel from "@mui/material/InputLabel";
import MenuItem from "@mui/material/MenuItem";
import Select from "@mui/material/Select";
import type { SelectChangeEvent } from "@mui/material/Select";
import { useCoatColors, useCoatPatterns, useCoatLengths } from "../hooks";

interface FilterState {
  coatColorId: string;
  coatPatternId: string;
  coatLengthId: string;
}

interface CatBreedFiltersProps {
  filters: FilterState;
  onFilterChange: (filters: FilterState) => void;
}

export function CatBreedFilters({
  filters,
  onFilterChange,
}: CatBreedFiltersProps) {
  const { data: colors } = useCoatColors();
  const { data: patterns } = useCoatPatterns();
  const { data: lengths } = useCoatLengths();

  const handleChange =
    (field: keyof FilterState) => (event: SelectChangeEvent) => {
      onFilterChange({
        ...filters,
        [field]: event.target.value,
      });
    };

  return (
    <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap", mb: 3 }}>
      <FormControl size="small" sx={{ minWidth: 150 }}>
        <InputLabel id="coat-color-label">{"毛色"}</InputLabel>
        <Select
          labelId="coat-color-label"
          value={filters.coatColorId}
          label={"毛色"}
          onChange={handleChange("coatColorId")}
          data-testid="filter-coat-color"
        >
          <MenuItem value="">{"すべて"}</MenuItem>
          {colors?.map((color) => (
            <MenuItem key={color.id} value={color.id}>
              {color.name}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      <FormControl size="small" sx={{ minWidth: 150 }}>
        <InputLabel id="coat-pattern-label">{"模様"}</InputLabel>
        <Select
          labelId="coat-pattern-label"
          value={filters.coatPatternId}
          label={"模様"}
          onChange={handleChange("coatPatternId")}
          data-testid="filter-coat-pattern"
        >
          <MenuItem value="">{"すべて"}</MenuItem>
          {patterns?.map((pattern) => (
            <MenuItem key={pattern.id} value={pattern.id}>
              {pattern.name}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      <FormControl size="small" sx={{ minWidth: 150 }}>
        <InputLabel id="coat-length-label">{"毛の長さ"}</InputLabel>
        <Select
          labelId="coat-length-label"
          value={filters.coatLengthId}
          label={"毛の長さ"}
          onChange={handleChange("coatLengthId")}
          data-testid="filter-coat-length"
        >
          <MenuItem value="">{"すべて"}</MenuItem>
          {lengths?.map((length) => (
            <MenuItem key={length.id} value={length.id}>
              {length.name}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
    </Box>
  );
}
