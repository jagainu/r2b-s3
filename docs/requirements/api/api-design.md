# API 設計書

## 概要

| 項目 | 内容 |
|------|------|
| プロジェクト | 猫の種類学習アプリ |
| ベースURL | `/api/v1` |
| 認証方式 | JWT（httpOnly Cookie）|
| フレームワーク | FastAPI（Python 3.11+） |
| レスポンス形式 | JSON |

### 認証ルール

| 種別 | 説明 |
|------|------|
| 認証必須 | `🔒` マーク。未認証時は `401 Unauthorized` を返す |
| 認証不要 | `🌐` マーク。未認証でもアクセス可能 |

### Cookie / CORS 方針

Vercel（フロントエンド）と API（ECS）は**別ドメイン**で運用するため、クロスオリジン Cookie を使用する。

```
Set-Cookie: access_token=<JWT>; HttpOnly; Secure; SameSite=None; Path=/; Max-Age=900
Set-Cookie: refresh_token=<JWT>; HttpOnly; Secure; SameSite=None; Path=/api/v1/auth/refresh; Max-Age=604800
```

| 設定 | 値 | 理由 |
|------|-----|------|
| SameSite | `None` | クロスオリジン Cookie 送信に必要 |
| Secure | 必須 | `SameSite=None` は HTTPS 必須 |
| access_token Max-Age | 900秒（15分） | 短命トークンで漏洩リスク低減 |
| refresh_token Path | `/api/v1/auth/refresh` のみ | 他エンドポイントへの自動送信を防止 |

**CORS 設定**
```
Access-Control-Allow-Origin: https://<vercel-domain>  （ワイルドカード不可）
Access-Control-Allow-Credentials: true
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
```

**CSRF 対策**：状態変更を伴うエンドポイント（POST/PUT/DELETE）には `X-CSRF-Token` ヘッダーを必須とする（二重送信 Cookie 方式）。

---

## エンドポイント一覧

| # | メソッド | パス | 説明 | 認証 | CSRF |
|---|---------|------|------|------|------|
| 1 | POST | `/auth/register` | 新規登録（メール＋パスワード） | 🌐 | - |
| 2 | POST | `/auth/login` | ログイン（メール＋パスワード） | 🌐 | - |
| 3 | POST | `/auth/google` | Google OAuth ログイン・登録 | 🌐 | - |
| 4 | POST | `/auth/logout` | ログアウト | 🔒 | ✅ |
| 5 | POST | `/auth/refresh` | アクセストークン更新 | 🌐（refresh Cookie） | - |
| 6 | GET | `/auth/me` | 自分のユーザー情報取得 | 🔒 | - |
| 7 | GET | `/cat-breeds` | 猫種一覧（フィルタ対応） | 🌐 | - |
| 8 | GET | `/cat-breeds/{id}` | 猫種詳細（写真・特徴込み） | 🌐 | - |
| 9 | GET | `/cat-breeds/{id}/similar` | 類似猫一覧 | 🌐 | - |
| 10 | GET | `/masters/coat-colors` | 毛色マスター一覧 | 🌐 | - |
| 11 | GET | `/masters/coat-patterns` | 模様マスター一覧 | 🌐 | - |
| 12 | GET | `/masters/coat-lengths` | 毛の長さマスター一覧 | 🌐 | - |
| 13 | GET | `/quiz/today` | 今日の一匹を取得 | 🔒 | - |
| 14 | POST | `/quiz/sessions` | クイズセッション生成（全問題をDB保存） | 🔒 | ✅ |
| 15 | POST | `/quiz/answer` | クイズ回答を送信（サーバー判定） | 🔒 | ✅ |
| 16 | POST | `/quiz/sessions/{session_id}/finalize` | セッション完了・結果をサーバー算出して保存 | 🔒 | ✅ |
| 17 | GET | `/users/me/stats` | ユーザー統計（累計覚えた種類数）取得 | 🔒 | - |
| 18 | GET | `/users/me/sessions/latest` | 最新セッション結果取得 | 🔒 | - |

---

## 認証系 API

### POST `/auth/register` 🌐

**Request Body**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "username": "さくら"
}
```

**Validation**
| フィールド | ルール |
|-----------|--------|
| email | 必須・メール形式・重複不可 |
| password | 必須・8文字以上 |
| username | 必須・2文字以上・20文字以内 |

**Response 201 Created**
```json
{ "id": "uuid", "email": "user@example.com", "username": "さくら" }
```

**副作用**：`users` INSERT / access_token + refresh_token Cookie 発行

---

### POST `/auth/login` 🌐

**Request Body**
```json
{ "email": "user@example.com", "password": "password123" }
```

**Response 200 OK**
```json
{ "id": "uuid", "email": "user@example.com", "username": "さくら" }
```

**Response 401 Unauthorized**
```json
{ "detail": "メールアドレスまたはパスワードが正しくありません" }
```

**副作用**：access_token + refresh_token Cookie 発行

---

### POST `/auth/google` 🌐

**Request Body**
```json
{
  "code": "google_authorization_code",
  "redirect_uri": "https://example.com/auth/callback"
}
```

**Response 200 OK**
```json
{ "id": "uuid", "email": "user@gmail.com", "username": "田中さくら" }
```

**処理フロー**：Google API でトークン交換 → `google_id` で既存ユーザー照合 → 未登録なら INSERT → Cookie 発行

**副作用**：`users` SELECT / INSERT（初回のみ）/ Cookie 発行

---

### POST `/auth/logout` 🔒 ✅CSRF

**Response 204 No Content**

**副作用**：access_token + refresh_token Cookie 削除

---

### POST `/auth/refresh` 🌐（refresh_token Cookie）

access_token の有効期限切れ時に新しい access_token を発行する。フロントは 401 受信時に自動呼び出しする。

**Request**：ボディなし。refresh_token Cookie を自動送信。

**Response 200 OK**：新しい access_token Cookie を発行。ボディなし。

**Response 401 Unauthorized**：refresh_token が無効・期限切れ → ログイン画面へリダイレクト。

**補足**：フロント（`mutator.ts`）は `401` を受信したら `/auth/refresh` を呼び出し、成功したら元のリクエストをリトライする。失敗したらログイン画面へ遷移する。

---

### GET `/auth/me` 🔒

**Response 200 OK**
```json
{ "id": "uuid", "email": "user@example.com", "username": "さくら" }
```

---

## 猫データ API

### GET `/cat-breeds` 🌐

全猫種一覧を取得する。クエリパラメータでANDフィルタリングが可能。

**Query Parameters**
| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| coat_color_id | UUID | No | 毛色でフィルタリング |
| coat_pattern_id | UUID | No | 模様でフィルタリング |
| coat_length_id | UUID | No | 毛の長さでフィルタリング |

**Response 200 OK**
```json
[
  {
    "id": "uuid",
    "name": "アメリカンショートヘア",
    "coat_color": { "id": "uuid", "name": "シルバー" },
    "coat_pattern": { "id": "uuid", "name": "タビー（縞）" },
    "coat_length": { "id": "uuid", "name": "短毛" },
    "thumbnail_url": "https://cdn.example.com/cats/ame-short/1.jpg"
  }
]
```

**参照テーブル**：`cat_breeds` JOIN `coat_colors`, `coat_patterns`, `coat_lengths`, `cat_photos`（display_order=1）

---

### GET `/cat-breeds/{id}` 🌐

猫種の詳細情報（写真一覧・特徴）を取得する。解説画面・猫詳細画面で使用。

**Response 200 OK**
```json
{
  "id": "uuid",
  "name": "アメリカンショートヘア",
  "coat_color": { "id": "uuid", "name": "シルバー" },
  "coat_pattern": { "id": "uuid", "name": "タビー（縞）" },
  "coat_length": { "id": "uuid", "name": "短毛" },
  "photos": [
    { "id": "uuid", "url": "https://cdn.example.com/cats/ame-short/1.jpg", "display_order": 1 },
    { "id": "uuid", "url": "https://cdn.example.com/cats/ame-short/2.jpg", "display_order": 2 }
  ]
}
```

**Response 404 Not Found**：`{ "detail": "Cat breed not found" }`

---

### GET `/cat-breeds/{id}/similar` 🌐

類似猫一覧（最大3件）を取得する。

**Response 200 OK**
```json
[
  { "id": "uuid", "name": "ブリティッシュショートヘア", "thumbnail_url": "https://..." },
  { "id": "uuid", "name": "スコティッシュフォールド", "thumbnail_url": "https://..." }
]
```

**処理フロー**
1. `similar_cats` から priority 降順で取得（DBトリガーで対称性保証済み）
2. 3件に満たない場合、毛色・模様・毛の長さが1つ以上一致する猫を自動抽出
3. 最大3件で返す

---

## マスターデータ API

### GET `/masters/coat-colors` / `/masters/coat-patterns` / `/masters/coat-lengths` 🌐

それぞれのマスター一覧を返す。図鑑画面のフィルタードロップダウンで使用。

**Response 200 OK（例：coat-colors）**
```json
[
  { "id": "uuid", "name": "シルバー" },
  { "id": "uuid", "name": "白" }
]
```

**キャッシュ**：CloudFront でキャッシュ可（静的マスターデータ）

---

## クイズ API

### GET `/quiz/today` 🔒

今日の一匹のクイズ問題を取得する。ホーム画面で使用。

**処理フロー**：日付 + ユーザーID をシードとして乱数生成 → 同日同ユーザーは同じ猫を返す → `quiz_sessions`（source=today）+ `quiz_questions` + `quiz_choices` を DB に保存して返す

**Response 200 OK**
```json
{
  "session_id": "uuid",
  "question_type": "photo_to_name",
  "question_number": 1,
  "photo_url": "https://cdn.example.com/cats/ame-short/1.jpg",
  "choices": [
    { "id": "uuid", "name": "アメリカンショートヘア" },
    { "id": "uuid", "name": "ブリティッシュショートヘア" },
    { "id": "uuid", "name": "スコティッシュフォールド" },
    { "id": "uuid", "name": "ロシアンブルー" }
  ]
}
```

**補足**：`correct_cat_breed_id` はレスポンスに含めない（DB のみ保持）。

---

### POST `/quiz/sessions` 🔒 ✅CSRF

クイズ全10問を一括生成し、DB に保存して問題リストを返す。クイズ画面の開始時に1回だけ呼び出す。

**Request Body**：なし（認証済みユーザーIDのみ使用）

**Response 201 Created**
```json
{
  "session_id": "uuid",
  "questions": [
    {
      "question_number": 1,
      "question_type": "photo_to_name",
      "photo_url": "https://cdn.example.com/cats/ame-short/1.jpg",
      "choices": [
        { "id": "uuid", "name": "アメリカンショートヘア" },
        { "id": "uuid", "name": "ブリティッシュショートヘア" },
        { "id": "uuid", "name": "スコティッシュフォールド" },
        { "id": "uuid", "name": "ロシアンブルー" }
      ]
    },
    {
      "question_number": 2,
      "question_type": "name_to_photo",
      "cat_name": "ペルシャ",
      "choices": [
        { "id": "uuid", "photo_url": "https://cdn.example.com/cats/persian/1.jpg" },
        { "id": "uuid", "photo_url": "https://cdn.example.com/cats/angora/1.jpg" },
        { "id": "uuid", "photo_url": "https://cdn.example.com/cats/ragdoll/1.jpg" },
        { "id": "uuid", "photo_url": "https://cdn.example.com/cats/maine-coon/1.jpg" }
      ]
    }
  ]
}
```

**処理フロー**
1. `wrong_answers` からユーザーの誤答履歴を取得
2. `wrong_count` を重みとして10種の猫を**重複なし**で選択
3. 各問題の出題形式・選択肢をランダム決定
4. `quiz_sessions`, `quiz_questions`, `quiz_choices` を DB に保存
5. `correct_cat_breed_id` は DB のみ保持（レスポンスには含めない）

**副作用**：`quiz_sessions` INSERT / `quiz_questions` INSERT / `quiz_choices` INSERT

---

### POST `/quiz/answer` 🔒 ✅CSRF

クイズ回答を送信する。**正解判定はサーバー側で `quiz_questions` を参照して行う**（クライアント申告値に依存しない）。

**Request Body**
```json
{
  "session_id": "uuid",
  "question_number": 3,
  "selected_cat_id": "uuid"
}
```

**Validation**
| フィールド | ルール |
|-----------|--------|
| session_id | 必須・自分のセッションであること |
| question_number | 必須・そのセッションに存在する問題番号 |
| selected_cat_id | 必須・そのセッションの選択肢に含まれる猫ID |
| 二重回答防止 | `quiz_answers.UNIQUE(session_id, question_number)` で DB レベルで防止 |

**Response 200 OK**
```json
{
  "is_correct": true,
  "correct_cat_id": "uuid"
}
```

**処理フロー**
1. `quiz_questions` から `correct_cat_breed_id` を取得（サーバー保持）
2. `correct_cat_breed_id == selected_cat_id` で判定
3. `quiz_answers` に INSERT（UNIQUE 制約で二重回答防止）
4. 不正解：`wrong_answers` に UPSERT（`wrong_count += 1, last_wrong_at = NOW()`）
5. 正解：`correct_answers` に INSERT（`ON CONFLICT DO NOTHING`）
6. 判定結果と `correct_cat_id` を返す（クライアントはここで初めて正解を知る）

**副作用**：`quiz_answers` INSERT / `wrong_answers` UPSERT（不正解時）/ `correct_answers` INSERT（正解時）

---

### POST `/quiz/sessions/{session_id}/finalize` 🔒 ✅CSRF

セッション完了時に呼び出す。**スコアはサーバーが `quiz_answers` を集計して算出**（クライアント申告値を一切使用しない）。

**Request Body**：なし

**Validation**
- `session_id` が自分のセッションであること
- `quiz_sessions.status = 'active'` であること（完了済みセッションへの再呼び出し防止）
- 全問題への回答が存在すること（`quiz_answers` の件数 = `total_questions`）

**Response 200 OK**
```json
{
  "session_id": "uuid",
  "source": "quiz",
  "correct_count": 7,
  "incorrect_count": 3,
  "correct_rate": 0.7,
  "completed_at": "2026-03-03T12:00:00Z"
}
```

**処理フロー**
1. `quiz_answers WHERE session_id = ?` を集計して `correct_count`, `incorrect_count` を算出
2. `quiz_sessions.status = 'completed'`, `completed_at = NOW()` を UPDATE
3. `session_results` に INSERT（`UNIQUE(session_id)` で重複防止）

**副作用**：`quiz_sessions` UPDATE / `session_results` INSERT

---

## ユーザー統計 API

### GET `/users/me/stats` 🔒

**Response 200 OK**
```json
{ "total_correct_breeds": 42 }
```

**処理フロー**：`COUNT(*) FROM correct_answers WHERE user_id = ?`

---

### GET `/users/me/sessions/latest` 🔒

最新のクイズセッション結果を取得する。結果画面（P006）で使用。

**Query Parameters**
| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| source | VARCHAR | Yes | `quiz` 固定（結果画面は常にクイズセッションを参照） |

**Response 200 OK**
```json
{
  "session_id": "uuid",
  "source": "quiz",
  "correct_count": 7,
  "incorrect_count": 3,
  "correct_rate": 0.7,
  "completed_at": "2026-03-03T12:00:00Z"
}
```

**Response 404 Not Found**：`{ "detail": "No session found" }`

**処理フロー**：`session_results WHERE user_id = ? AND source = ? ORDER BY completed_at DESC LIMIT 1`

---

## 共通エラーレスポンス

| ステータス | 意味 | 例 |
|-----------|------|-----|
| 400 | バリデーションエラー | メール形式不正・パスワード短い |
| 401 | 未認証 | Cookie なし / access_token 期限切れ（→ /auth/refresh へ） |
| 403 | 権限なし | 他ユーザーのセッションへのアクセス |
| 404 | リソース不存在 | 存在しない猫ID |
| 409 | 重複 | 登録済みメールアドレス / 二重回答 |
| 422 | リクエスト形式エラー | FastAPI デフォルト |
| 500 | サーバーエラー | 予期せぬ例外 |

```json
{ "detail": "エラーメッセージ" }
```

---

## API と画面の対応表

| 画面 | 使用する API |
|------|------------|
| P007 ログイン・登録 | `POST /auth/register`, `POST /auth/login`, `POST /auth/google` |
| P001 ホーム | `GET /auth/me`, `GET /quiz/today`, `POST /quiz/answer`, `POST /quiz/sessions/{id}/finalize` |
| P002 クイズ | `POST /quiz/sessions`, `POST /quiz/answer` |
| P003 解説 | `GET /cat-breeds/{id}`, `GET /cat-breeds/{id}/similar`, `POST /quiz/sessions/{id}/finalize`（10問完了時） |
| P004 猫図鑑 | `GET /cat-breeds`, `GET /masters/coat-colors`, `GET /masters/coat-patterns`, `GET /masters/coat-lengths` |
| P005 猫詳細 | `GET /cat-breeds/{id}` |
| P006 結果 | `GET /users/me/sessions/latest?source=quiz`, `GET /users/me/stats` |

---

## キャッシュ方針

| エンドポイント | キャッシュ |
|--------------|---------|
| `/cat-breeds*`, `/masters/*` | CloudFront キャッシュ可（静的マスターデータ） |
| `/quiz/*`, `/users/*` | キャッシュなし（ユーザー固有データ） |
| `/auth/*` | キャッシュなし |
