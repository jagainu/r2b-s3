# Sprint 3 実装計画（Phase 1～3）

## 概要

このドキュメントは、Foundation Phase（Slice 0-1～0-6）の完了後、
Phase 1～3 の Feature 開発を計画したものです。

Vertical Slice Architecture（VSA）に基づいて機能を分割し、
フロントエンド（Next.js 15）とバックエンド（FastAPI）を並行して開発します。

## 前提条件

✅ **Foundation Phase（Slice 0-1～0-6）完了済み**
- FastAPI バックエンド初期化（app/main.py、ルーター登録）
- PostgreSQL Docker セットアップ（14テーブル・マイグレーション完了）
- JWT 認証・CSRF対策実装（httpOnly Cookie、二重送信 Cookie 方式）
- Next.js 15 フロントエンド初期化（App Router、MUI + TanStack Query）
- OpenAPI 出力・orval 自動生成統合

✅ **Slice 0-7 完了済み**
- Terraform IaC（AWS ECS、RDS、ECR、VPC等）

詳細は `docs/handoff.md` を参照してください。

---

## Phase 1: 基本機能

### Slice 1: 猫データマスター取得・図鑑画面

**概要**

全猫種一覧・マスターデータ取得・フィルタリング・図鑑表示の実装。
認証不要で誰でもアクセスできる基本情報機能。

**対象画面（フロント）**
- P004 猫図鑑画面（全猫種・フィルタドロップダウン・リスト表示）
- P005 猫詳細画面（写真カルーセル・特徴表示）

**API エンドポイント（バック）**
- `GET /cat-breeds` （クエリパラメータ: coat_color_id, coat_pattern_id, coat_length_id）
- `GET /cat-breeds/{id}` （詳細・写真一覧・特徴）
- `GET /cat-breeds/{id}/similar` （類似猫一覧）
- `GET /masters/coat-colors` （毛色マスター）
- `GET /masters/coat-patterns` （模様マスター）
- `GET /masters/coat-lengths` （毛の長さマスター）

**関連データ**
- cat_breeds（猫種マスター）
- cat_photos（猫写真）
- coat_colors, coat_patterns, coat_lengths（属性マスター）
- similar_cats（類似猫対応）

**実装順序**
1. バックエンド: リポジトリ層（猫種・写真・マスター取得 SQL）→ サービス層（フィルタリングロジック）→ API エンドポイント
2. フロントエンド: API フック（orval 生成の wrap）→ UI コンポーネント（リスト・詳細・カルーセル）
3. 統合テスト（フィルタリング検証、画像表示確認）

**チェックリスト**
- [ ] バックエンド: マスター取得 API 実装・テスト完了
- [ ] バックエンド: フィルタリング SQL 実装・テスト完了
- [ ] バックエンド: 類似猫 API 実装・テスト完了
- [ ] フロントエンド: 猫図鑑画面（リスト・フィルタ・検索）完成
- [ ] フロントエンド: 猫詳細画面（カルーセル・情報）完成
- [ ] API 疎通確認完了
- [ ] 統合テスト完了

**参考**
- `docs/requirements/specifications/猫図鑑画面.md`
- `docs/requirements/specifications/猫詳細画面.md`
- `docs/requirements/database/database-design.md` （14テーブル・ER図）

---

### Slice 2: ログイン・登録画面 UI + メール・Google 認証エンドポイント

**概要**

メール＋パスワード / Google OAuth によるログイン・新規登録の完全実装。
認証ミドルウェア（JWT・CSRF）と連携。

**対象画面（フロント）**
- P007 ログイン・登録画面（タブ切り替え・フォーム・Google ボタン）

**API エンドポイント（バック）**
- `POST /auth/register` （メール＋パスワード＋ユーザー名で新規登録）
- `POST /auth/login` （メール＋パスワードでログイン）
- `POST /auth/google` （Google OAuth 認可コードで認証）
- `GET /auth/me` （認証済みユーザー情報取得）
- `GET /auth/csrf` （CSRF トークン配布）

**関連データ**
- users（ユーザー情報・認証情報）

**実装順序**
1. バックエンド: リポジトリ層（ユーザー照合・作成）→ サービス層（バリデーション・bcrypt ハッシュ・JWT 発行）→ API エンドポイント
2. フロントエンド: ログイン・登録フォーム（バリデーション）→ Google OAuth リンク → Cookie 自動処理（mutator）
3. 統合テスト（CSRF トークン検証、Cookie secure 設定確認、401 リトライ）

**チェックリスト**
- [ ] バックエンド: メールユーザー登録 API 実装・テスト完了
- [ ] バックエンド: メールログイン API 実装・テスト完了
- [ ] バックエンド: Google OAuth API 実装・テスト完了
- [ ] バックエンド: ユーザー情報取得 API 実装・テスト完了
- [ ] バックエンド: CSRF トークン配布 API 実装・テスト完了
- [ ] フロントエンド: ログイン画面 UI 完成（メール・Google ボタン）
- [ ] フロントエンド: 登録画面 UI 完成（バリデーション）
- [ ] フロントエンド: Cookie 自動処理（mutator）検証完了
- [ ] API 疎通確認完了
- [ ] 統合テスト完了（CSRF、secure Cookie、401 リトライ）

**参考**
- `docs/requirements/specifications/ログイン・登録画面.md`
- `CLAUDE.md` → 3レイヤードアーキテクチャ（認証セクション）

---

## Phase 2: クイズ基本機能

### Slice 3: クイズセッション生成・問題出題

**概要**

クイズセッション作成・10問一括生成・誤答履歴を考慮した優先出題。
ユーザーが「クイズを始める」ボタンをクリックすると、10問分の問題をサーバー側で一括生成。

**対象画面（フロント）**
- P001 ホーム画面（「クイズを始める」ボタン）
- P002 クイズ画面（問題リスト・進捗表示・4択選択肢）

**API エンドポイント（バック）**
- `POST /quiz/sessions` （セッション生成・10問一括作成・選択肢生成）
- `GET /quiz/today` （今日の一匹：日付+ユーザーIDをシードにランダム猫を選択）

**関連データ**
- quiz_sessions（セッション管理）
- quiz_questions（出題問題・正解保持（クライアント非公開））
- quiz_choices（各問題の選択肢）
- wrong_answers（誤答履歴：優先出題に使用）
- cat_breeds, cat_photos（猫データ）

**実装順序**
1. バックエンド: リポジトリ層（セッション・問題・選択肢作成）→ サービス層（誤答優先ロジック・ランダム猫選択・問題形式割り当て）→ API エンドポイント
2. フロントエンド: セッション開始フロー（POST /quiz/sessions）→ 問題リスト表示 → 進捗表示（X/10）
3. 統合テスト（誤答優先出題検証、form 形式（photo_to_name / name_to_photo）のランダム割り当て検証）

**チェックリスト**
- [ ] バックエンド: セッション作成・問題生成 API 実装・テスト完了
- [ ] バックエンド: 誤答優先ロジック実装・テスト完了
- [ ] バックエンド: 問題形式（photo_to_name / name_to_photo）ランダム割り当て実装・テスト完了
- [ ] バックエンド: 今日の一匹 API 実装・テスト完了（日付シード検証）
- [ ] フロントエンド: ホーム画面「クイズを始める」フロー完成
- [ ] フロントエンド: クイズ画面（問題表示・選択肢表示・進捗）完成
- [ ] フロントエンド: 今日の一匹表示・回答フロー完成
- [ ] API 疎通確認完了
- [ ] 統合テスト完了（問題形式・誤答優先検証）

**参考**
- `docs/requirements/specifications/クイズ画面.md`
- `docs/requirements/ipo/ipo.md` → IPO #4, #5, #7, #8
- `CLAUDE.md` → VSA ガイド・TDD ガイド

---

### Slice 4: クイズ回答・採点・履歴記録

**概要**

ユーザーの回答を受け取り、サーバー側で正解判定・履歴記録・誤答/正解リスト更新。
解説画面を表示し、次問題へ進むまでのフロー。セッション完了時は結果算出。

**対象画面（フロント）**
- P002 クイズ画面（4択クリック・回答送信）
- P003 解説画面（正解表示・猫情報・類似猫・「次の問題へ」ボタン）

**API エンドポイント（バック）**
- `POST /quiz/answer` （回答送信→サーバー採点→履歴記録→JSON で正誤フラグ返却）
- `POST /quiz/sessions/{session_id}/finalize` （セッション完了→結果算出→session_results に INSERT）

**関連データ**
- quiz_answers（回答ログ）
- wrong_answers（誤答履歴：UPSERT 更新）
- correct_answers（正解履歴：INSERT）
- session_results（セッション結果：サーバー算出 correct_count / incorrect_count）
- cat_breeds, similar_cats（猫データ・類似猫）

**実装順序**
1. バックエンド: リポジトリ層（回答・履歴保存）→ サービス層（正誤判定・wrong_answers UPSERT・correct_answers INSERT・結果集計）→ API エンドポイント
2. フロントエンド: 回答送信フロー（POST /quiz/answer）→ 解説表示（正解フラグ・猫情報・類似猫）→ 次問題遷移
3. 統合テスト（二重回答防止・スコア改ざん防止・result 算出検証）

**チェックリスト**
- [ ] バックエンド: 回答受信・採点 API 実装・テスト完了
- [ ] バックエンド: wrong_answers UPSERT ロジック実装・テスト完了
- [ ] バックエンド: correct_answers INSERT ロジック実装・テスト完了
- [ ] バックエンド: セッション finalize・結果算出 API 実装・テスト完了
- [ ] バックエンド: 二重回答防止（UNIQUE 制約）検証完了
- [ ] フロントエンド: クイズ画面回答送信・解説表示フロー完成
- [ ] フロントエンド: 解説画面（正解表示・猫詳細・類似猫）完成
- [ ] フロントエンド: 「次の問題へ」→ 次問題またはP006遷移完成
- [ ] API 疎通確認完了
- [ ] 統合テスト完了（二重回答・スコア改ざん防止検証）

**参考**
- `docs/requirements/specifications/解説画面.md`
- `docs/requirements/ipo/ipo.md` → IPO #6, #9, #11, #12, #13, #14
- `docs/handoff.md` → 「スコア改ざん防止」セクション

---

## Phase 3: ユーザー統計・結果表示

### Slice 5: 結果表示・累計統計

**概要**

セッション完了後の結果表示（正答率・正解数・不正解数）。
ユーザーが覚えた猫種の累計数をホーム画面・結果画面で表示。

**対象画面（フロント）**
- P006 結果画面（正答率・正解数・不正解数・「もう一度挑戦」ボタン）
- P001 ホーム画面（累計覚えた種類数バッジ表示）

**API エンドポイント（バック）**
- `GET /users/me/stats` （ユーザー統計：覚えた種類の累計数）
- `GET /users/me/sessions/latest` （最新セッション結果）
- `GET /users/me/sessions/latest?source=quiz` （quiz セッションの最新結果）

**関連データ**
- session_results（セッション結果：正解数・不正解数）
- correct_answers（正解した猫種一覧：ユニーク数をカウント）
- quiz_answers（回答ログ：確認用）

**実装順序**
1. バックエンド: リポジトリ層（統計集計 SQL）→ サービス層（計算ロジック）→ API エンドポイント
2. フロントエンド: 結果画面表示（セッション結果表示）→ 統計フック（TanStack Query キャッシュ）→ ホーム画面に統計バッジ
3. 統合テスト（累計数計算正確性・結果表示）

**チェックリスト**
- [ ] バックエンド: ユーザー統計 API 実装・テスト完了
- [ ] バックエンド: 最新セッション結果取得 API 実装・テスト完了
- [ ] フロントエンド: 結果画面（正答率・正解数・不正解数）完成
- [ ] フロントエンド: 「もう一度挑戦」ボタンフロー完成
- [ ] フロントエンド: ホーム画面統計表示完成
- [ ] API 疎通確認完了
- [ ] 統合テスト完了

**参考**
- `docs/requirements/specifications/結果画面.md`
- `docs/requirements/ipo/ipo.md` → IPO #20, #21, #22

---

## 依存関係マップ

```
✅ Foundation Phase 完了（Slice 0-1～0-6）
         ↓

┌──────────────────────────────────────┐
│ Phase 1: 基本機能                      │
├──────────────────────────────────────┤
│ Slice 1: 猫データマスター取得・図鑑   │（認証不要）
│ Slice 2: ログイン・登録 UI + 認証     │（メール・Google）
└──────────────────────────────────────┘
         ↓
┌──────────────────────────────────────┐
│ Phase 2: クイズ機能                   │
├──────────────────────────────────────┤
│ Slice 3: セッション生成・問題出題    │
│          ↑ 依存: Slice 1, 2
│
│ Slice 4: 回答・採点・履歴記録         │
│          ↑ 依存: Slice 3
└──────────────────────────────────────┘
         ↓
┌──────────────────────────────────────┐
│ Phase 3: 統計・結果表示              │
├──────────────────────────────────────┤
│ Slice 5: 結果表示・累計統計          │
│          ↑ 依存: Slice 4
└──────────────────────────────────────┘
```

**並列開発可能な組み合わせ**
- Slice 1 と Slice 2 は独立して並列開発可能
- Slice 3 と Slice 4 は順次（Slice 3 完了後に Slice 4）
- Slice 5 は Slice 4 完了後

---

## 開発環境起動

```bash
# 1. DB起動（既に完了）
docker compose up -d

# 2. Backend サーバー起動
cd backend && uv run uvicorn app.main:app --reload --port 8000

# 3. Frontend 開発サーバー起動（別ウィンドウ）
cd frontend && bun run dev

# 4. 動作確認
curl http://localhost:8000/api/v1/health
open http://localhost:3000
```

---

## OpenAPI 統合ワークフロー

各スライス実装時、以下を順守してください：

```bash
# Backend 実装後、OpenAPI スキーマを出力
cd backend && uv run python scripts/export_openapi.py

# orval で TypeScript API client を自動生成
cd ../frontend && bun run orval

# Frontend 実装で自動生成フックを使用
# src/shared/api/generated/index.ts が更新される
```

---

## アーキテクチャ参照

- **Vertical Slice Architecture（VSA）**: `.claude/rules/vsa-guide.md`
- **3レイヤードアーキテクチャ**: `.claude/rules/three-layer-architecture.md`
- **TDD**: `.claude/rules/tdd-guide.md`
- **プロジェクト設定**: `CLAUDE.md`

---

## 計画の実行フロー

### ステップ 1: Slice 1・2 並列実装

```bash
# ターミナル 1: Slice 1 実装
/fullstack-integration Slice 1: 猫データマスター取得・図鑑画面

# ターミナル 2: Slice 2 実装（並列）
/fullstack-integration Slice 2: ログイン・登録 UI + 認証
```

### ステップ 2: Slice 3 実装

```bash
/fullstack-integration Slice 3: クイズセッション生成・問題出題
```

### ステップ 3: Slice 4 実装

```bash
/fullstack-integration Slice 4: クイズ回答・採点・履歴記録
```

### ステップ 4: Slice 5 実装

```bash
/fullstack-integration Slice 5: 結果表示・累計統計
```

### ステップ 5: 統合テスト・コミット

各スライス完了時に以下を実行：

```bash
# 品質チェック（linter, formatter, test）
/git-commit

# またはコマンドラインで
cd backend && uv run pytest
cd ../frontend && bun run typecheck
```

---

## 計画の修正

計画を変更する場合は `/planner` を再度実行してください。

---

**生成日時**: 2026-03-04
**エージェント**: planner
