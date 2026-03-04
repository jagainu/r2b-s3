"use client";

import { useQuery } from "@tanstack/react-query";
import type {
  CatBreedDetailResponse,
  CatBreedListItem,
  GetCatBreedsApiV1CatBreedsGetParams,
  MasterItemResponse,
  SimilarCatResponse,
} from "@/shared/api/generated";
import {
  fetchCatBreeds,
  fetchCatBreedDetail,
  fetchSimilarCats,
  fetchCoatColors,
  fetchCoatPatterns,
  fetchCoatLengths,
} from "./api";

/** 猫種一覧を取得する hook */
export function useCatBreeds(params?: GetCatBreedsApiV1CatBreedsGetParams) {
  return useQuery<CatBreedListItem[]>({
    queryKey: ["cat-breeds", params],
    queryFn: async () => {
      const res = await fetchCatBreeds(params);
      return res.data;
    },
  });
}

/** 猫種詳細を取得する hook */
export function useCatBreedDetail(breedId: string | undefined) {
  return useQuery<CatBreedDetailResponse>({
    queryKey: ["cat-breed-detail", breedId],
    queryFn: async () => {
      const res = await fetchCatBreedDetail(breedId!);
      return res.data;
    },
    enabled: !!breedId,
  });
}

/** 類似猫リストを取得する hook */
export function useSimilarCats(breedId: string | undefined) {
  return useQuery<SimilarCatResponse[]>({
    queryKey: ["similar-cats", breedId],
    queryFn: async () => {
      const res = await fetchSimilarCats(breedId!);
      return res.data;
    },
    enabled: !!breedId,
  });
}

/** 毛色マスター一覧を取得する hook */
export function useCoatColors() {
  return useQuery<MasterItemResponse[]>({
    queryKey: ["coat-colors"],
    queryFn: async () => {
      const res = await fetchCoatColors();
      return res.data;
    },
    staleTime: 5 * 60 * 1000, // マスターデータは5分キャッシュ
  });
}

/** 模様マスター一覧を取得する hook */
export function useCoatPatterns() {
  return useQuery<MasterItemResponse[]>({
    queryKey: ["coat-patterns"],
    queryFn: async () => {
      const res = await fetchCoatPatterns();
      return res.data;
    },
    staleTime: 5 * 60 * 1000,
  });
}

/** 毛の長さマスター一覧を取得する hook */
export function useCoatLengths() {
  return useQuery<MasterItemResponse[]>({
    queryKey: ["coat-lengths"],
    queryFn: async () => {
      const res = await fetchCoatLengths();
      return res.data;
    },
    staleTime: 5 * 60 * 1000,
  });
}
