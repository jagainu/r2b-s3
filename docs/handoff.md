# 引き継ぎ資料 — 2026-03-03

## 進捗サマリー

| フェーズ | 内容 | 状態 |
|---------|------|------|
| Sprint 3 設計フェーズ（全14ステップ） | ビジネス要件〜API設計・実装設計レビュー | ✅ 完了 |
| Foundation Phase（Slice 0-1〜0-6） | FastAPI + PostgreSQL + Next.js 基盤構築 | ✅ 完了 |
| Feature 開発（Slice 1〜） | 各機能の実装 | 🔜 **次のステップ** |

---

## 設計ドキュメント（`docs/requirements/`）

| ファイル | 内容 |
|---------|------|
| `business-requirements/business-requirements.md` | v1/v2 成功基準（v2 は必達要件） |
| `ipo/ipo.md` | 全22機能の Input/Process/Output 定義 |
| `database/database-design.md` | 14テーブル・ER図・制約・インデックス |
| `api/api-design.md` | 19エンドポイント（認証・猫データ・クイズ・ユーザー） |
| `requirements-v2/*.md` | 7画面の要件定義（DBテーブル対応付き） |
| `data/data-list.md` | 全データ項目一覧（67項目） |

---

## 実装済み（Foundation Phase）

### Backend（`backend/`）

```
app/
├── main.py                  FastAPI アプリ・CORS・ルーター登録
├── core/
│   ├── config.py            環境変数（DATABASE_URL, JWT_SECRET 等）
│   ├── database.py          AsyncEngine + AsyncSession + Base
│   ├── dependencies.py      CurrentUser / CsrfVerified / DbSession
│   └── security.py          JWT 発行・検証・bcrypt・CSRF ヘルパー
├── models/
│   ├── base.py              Base + TimestampMixin
│   ├── user.py              User
│   ├── masters.py           CoatColor / CoatPattern / CoatLength / CatBreed / CatPhoto / SimilarCat
│   └── quiz.py              QuizSession / QuizQuestion / QuizChoice / QuizAnswer / WrongAnswer / CorrectAnswer / SessionResult
├── api/v1/endpoints/
│   ├── health.py            GET /api/v1/health
│   └── auth.py              register / login / logout / refresh / csrf / me
├── api/v1/schemas/
│   └── auth.py              RegisterRequest / LoginRequest / UserResponse / CsrfResponse
└── repositories/
    └── user_repository.py   get_by_id / get_by_email / create
alembic/versions/
└── a5836e42c97a_initial_schema.py  全14テーブル + similar_cats DBトリガー
```

**テスト**: 11/11 PASS（`uv run pytest`）

### DB（PostgreSQL Docker）

```
コンテナ名: catbreed_db
DB名:       catbreed_db
ユーザー:   postgres / postgres
ポート:     5432
```

起動: `docker compose up -d`

### Frontend（`frontend/`）

```
src/
├── app/
│   ├── layout.tsx            Root Layout（Providers でラップ）
│   ├── page.tsx              トップページ
│   ├── (auth)/login/         ログインページ
│   └── (portal)/dashboard/  ダッシュボード
├── shared/
│   ├── api/
│   │   ├── mutator.ts        CSRF自動付与・204ハンドリング・401リトライ済み
│   │   └── generated/        orval 自動生成（編集禁止）
│   └── ui/
│       ├── theme.ts          MUI テーマ
│       └── Providers.tsx     MUI + TanStack Query プロバイダー
```

**型チェック**: `bun run typecheck` エラーなし

### OpenAPI 統合

```bash
# Backend 変更後
cd backend && uv run python scripts/export_openapi.py  # → openapi.json 更新
cd ../frontend && bun run orval                         # → generated/index.ts 更新
```

---

## 主要な設計決定事項

| 決定事項 | 内容 |
|---------|------|
| クイズ正解情報 | `quiz_questions.correct_cat_breed_id` をサーバー保持・クライアント非公開 |
| スコア算出 | `POST /quiz/sessions/{id}/finalize` でサーバーが `quiz_answers` を集計 |
| 二重回答防止 | `UNIQUE(session_id, question_number)` on `quiz_answers` |
| CSRF対策 | 二重送信 Cookie 方式（`GET /auth/csrf` → `X-CSRF-Token` ヘッダー） |
| Cookie設定 | `SameSite=None; Secure`（Vercel ↔ ECS クロスオリジン） |
| similar_cats対称性 | DBトリガーで自動保証 |

---

## 次のステップ

### 1. 実装計画策定（planner エージェント）

```
planner で Feature 開発の計画を立ててください
```

→ `docs/detail-plan.md` に VSA スライス一覧が生成されます。

### 2. Feature 実装（fullstack-integration）

```
/fullstack-integration Slice 1: {機能名}
```

→ Backend（schema → test → repo/service/api）+ Frontend（feature → test → component）を一気通貫で実装。

**優先度高い機能（IPO順）:**
1. 猫種一覧・詳細 API（`GET /cat-breeds`, `GET /cat-breeds/{id}`）
2. ログイン・登録画面 UI
3. クイズセッション生成（`POST /quiz/sessions`）
4. クイズ回答（`POST /quiz/answer`）
5. 今日の一匹（`GET /quiz/today`）
6. 解説画面・結果画面

---

## ローカル開発の起動手順

```bash
# 1. DB起動
docker compose up -d

# 2. Backend
cd backend && uv run uvicorn app.main:app --reload --port 8000

# 3. Frontend
cd frontend && bun run dev

# 確認
curl http://localhost:8000/api/v1/health  # → {"status":"ok"}
open http://localhost:3000
```
