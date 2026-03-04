# Slice 5: 結果表示・累計統計

## Phase 1: Backend

### 1.1 Schema 設計
- [x] `app/api/v1/schemas/users.py` - UserStatsResponse, LatestSessionResponse 作成

### 1.2 Repository 層（TDD）
- [x] RED: `tests/test_user_stats_repository.py` テスト作成（4件）
- [x] GREEN: `app/repositories/user_stats_repository.py` 実装

### 1.3 Service 層（TDD）
- [x] RED: `tests/test_user_stats_service.py` テスト作成（5件）
- [x] GREEN: `app/services/user_stats_service.py` 実装

### 1.4 API 層（TDD）
- [x] RED: `tests/test_users_api.py` テスト作成（5件）
- [x] GREEN: `app/api/v1/endpoints/users.py` 実装
- [x] ルーター登録（`app/api/v1/__init__.py`）

### 1.5 Backend 品質チェック
- [x] ruff format + check
- [x] pytest 全テスト通過（14件追加、合計 120+件）

## Phase 2: Integration
- [x] OpenAPI スキーマ出力（20エンドポイント）
- [x] orval 再生成
- [x] TypeScript 型チェック通過

## Phase 3: Frontend

### 3.1 Feature 構成
- [x] `src/features/quiz/api.ts` - fetchUserStats, fetchLatestSession 追加
- [x] `src/features/quiz/hooks.ts` - useUserStats, useLatestSession 追加
- [x] `src/features/quiz/index.ts` - barrel export 更新

### 3.2 Components
- [x] `ResultPage.tsx` - P006 結果画面（正答率・正解数・不正解数・累計バッジ・ボタン3つ）
- [x] `HomePage.tsx` - 統計バッジ追加（累計覚えた種類数）

### 3.3 ページ接続
- [x] `src/app/(portal)/quiz/result/page.tsx` - P006 結果画面ルート

### 3.4 Frontend 品質チェック
- [x] typecheck 通過

## Phase 4: Final Check
- [x] Backend テスト全通過（Slice 5 の 14件全パス）
- [x] Frontend TypeScript 型チェック通過
- [x] ruff format + check パス
