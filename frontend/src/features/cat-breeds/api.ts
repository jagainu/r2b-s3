/**
 * cat-breeds feature の API ラッパー
 *
 * orval 生成関数を wrap し、customInstance (mutator) 経由で呼び出す。
 * Cookie 認証・CSRF は mutator が自動処理する。
 */

import { customInstance } from "@/shared/api/mutator";
import type {
  CatBreedDetailResponse,
  CatBreedListItem,
  GetCatBreedsApiV1CatBreedsGetParams,
  MasterItemResponse,
  SimilarCatResponse,
} from "@/shared/api/generated";
import {
  getGetCatBreedsApiV1CatBreedsGetUrl,
  getGetCatBreedDetailApiV1CatBreedsBreedIdGetUrl,
  getGetSimilarCatsApiV1CatBreedsBreedIdSimilarGetUrl,
  getGetCoatColorsApiV1MastersCoatColorsGetUrl,
  getGetCoatPatternsApiV1MastersCoatPatternsGetUrl,
  getGetCoatLengthsApiV1MastersCoatLengthsGetUrl,
} from "@/shared/api/generated";

// 共通レスポンス型
interface ApiResponse<T> {
  data: T;
  status: number;
  headers: Headers;
}

/** 猫種一覧を取得する */
export const fetchCatBreeds = (
  params?: GetCatBreedsApiV1CatBreedsGetParams,
): Promise<ApiResponse<CatBreedListItem[]>> => {
  return customInstance<ApiResponse<CatBreedListItem[]>>(
    getGetCatBreedsApiV1CatBreedsGetUrl(params),
  );
};

/** 猫種詳細を取得する */
export const fetchCatBreedDetail = (
  breedId: string,
): Promise<ApiResponse<CatBreedDetailResponse>> => {
  return customInstance<ApiResponse<CatBreedDetailResponse>>(
    getGetCatBreedDetailApiV1CatBreedsBreedIdGetUrl(breedId),
  );
};

/** 類似猫リストを取得する */
export const fetchSimilarCats = (
  breedId: string,
): Promise<ApiResponse<SimilarCatResponse[]>> => {
  return customInstance<ApiResponse<SimilarCatResponse[]>>(
    getGetSimilarCatsApiV1CatBreedsBreedIdSimilarGetUrl(breedId),
  );
};

/** 毛色マスター一覧を取得する */
export const fetchCoatColors = (): Promise<
  ApiResponse<MasterItemResponse[]>
> => {
  return customInstance<ApiResponse<MasterItemResponse[]>>(
    getGetCoatColorsApiV1MastersCoatColorsGetUrl(),
  );
};

/** 模様マスター一覧を取得する */
export const fetchCoatPatterns = (): Promise<
  ApiResponse<MasterItemResponse[]>
> => {
  return customInstance<ApiResponse<MasterItemResponse[]>>(
    getGetCoatPatternsApiV1MastersCoatPatternsGetUrl(),
  );
};

/** 毛の長さマスター一覧を取得する */
export const fetchCoatLengths = (): Promise<
  ApiResponse<MasterItemResponse[]>
> => {
  return customInstance<ApiResponse<MasterItemResponse[]>>(
    getGetCoatLengthsApiV1MastersCoatLengthsGetUrl(),
  );
};
