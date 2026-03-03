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

---

## エンドポイント一覧

| # | メソッド | パス | 説明 | 認証 |
|---|---------|------|------|------|
| 1 | POST | `/auth/register` | 新規登録（メール＋パスワード） | 🌐 |
| 2 | POST | `/auth/login` | ログイン（メール＋パスワード） | 🌐 |
| 3 | POST | `/auth/google` | Google OAuth ログイン・登録 | 🌐 |
| 4 | POST | `/auth/logout` | ログアウト | 🔒 |
| 5 | GET | `/auth/me` | 自分のユーザー情報取得 | 🔒 |
| 6 | GET | `/cat-breeds` | 猫種一覧（フィルタ対応） | 🌐 |
| 7 | GET | `/cat-breeds/{id}` | 猫種詳細（写真・特徴込み） | 🌐 |
| 8 | GET | `/cat-breeds/{id}/similar` | 類似猫一覧 | 🌐 |
| 9 | GET | `/masters/coat-colors` | 毛色マスター一覧 | 🌐 |
| 10 | GET | `/masters/coat-patterns` | 模様マスター一覧 | 🌐 |
| 11 | GET | `/masters/coat-lengths` | 毛の長さマスター一覧 | 🌐 |
| 12 | GET | `/quiz/today` | 今日の一匹を取得 | 🔒 |
| 13 | GET | `/quiz/session` | クイズ全10問を一括生成・取得 | 🔒 |
| 14 | POST | `/quiz/answer` | クイズ回答を送信 | 🔒 |
| 15 | GET | `/users/me/stats` | ユーザー統計（累計覚えた種類数）取得 | 🔒 |
| 16 | POST | `/users/me/sessions` | セッション結果を保存 | 🔒 |
| 17 | GET | `/users/me/sessions/latest` | 最新セッション結果取得 | 🔒 |

---

## 認証系 API

### POST `/auth/register` 🌐

メールアドレス・パスワード・ユーザー名で新規登録する。

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
{
  "id": "uuid",
  "email": "user@example.com",
  "username": "さくら"
}
```

**Response 400 Bad Request**（バリデーションエラー）
```json
{ "detail": "このメールアドレスはすでに使用されています" }
```

**副作用**：`users` INSERT / JWT Cookie 発行

---

### POST `/auth/login` 🌐

メールアドレスとパスワードでログインする。

**Request Body**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response 200 OK**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "username": "さくら"
}
```

**Response 401 Unauthorized**
```json
{ "detail": "メールアドレスまたはパスワードが正しくありません" }
```

**副作用**：JWT Cookie 発行

---

### POST `/auth/google` 🌐

Google OAuth の認可コードを受け取り、ログインまたは自動新規登録する。

**Request Body**
```json
{
  "code": "google_authorization_code",
  "redirect_uri": "https://example.com/auth/callback"
}
```

**Response 200 OK**
```json
{
  "id": "uuid",
  "email": "user@gmail.com",
  "username": "田中さくら"
}
```

**処理フロー**
1. Google API でトークン交換・ユーザー情報取得
2. `users.google_id` で既存ユーザーを照合
3. 未登録の場合は自動 INSERT（username は Google display_name を使用）
4. JWT Cookie 発行

**副作用**：`users` SELECT / INSERT（初回のみ） / JWT Cookie 発行

---

### POST `/auth/logout` 🔒

JWT Cookie を削除してログアウトする。

**Response 204 No Content**

**副作用**：JWT Cookie 削除

---

### GET `/auth/me` 🔒

現在ログイン中のユーザー情報を取得する。

**Response 200 OK**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "username": "さくら"
}
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

**Response 404 Not Found**
```json
{ "detail": "Cat breed not found" }
```

**参照テーブル**：`cat_breeds` JOIN `coat_colors`, `coat_patterns`, `coat_lengths` + `cat_photos`

---

### GET `/cat-breeds/{id}/similar` 🌐

類似猫一覧（最大3件）を取得する。解説画面で使用。

**Response 200 OK**
```json
[
  {
    "id": "uuid",
    "name": "ブリティッシュショートヘア",
    "thumbnail_url": "https://cdn.example.com/cats/british-short/1.jpg"
  },
  {
    "id": "uuid",
    "name": "スコティッシュフォールド",
    "thumbnail_url": "https://cdn.example.com/cats/scottish-fold/1.jpg"
  }
]
```

**処理フロー**
1. `similar_cats` から手動登録（priority > 0）を priority 降順で取得
2. 3件に満たない場合、毛色・模様・毛の長さが1つ以上一致する猫を `cat_breeds` から自動抽出
3. 最大3件にトリミングして返す

**参照テーブル**：`similar_cats`, `cat_breeds`, `cat_photos`

---

## マスターデータ API

### GET `/masters/coat-colors` 🌐

毛色マスター一覧を取得する。図鑑画面のフィルタードロップダウンで使用。

**Response 200 OK**
```json
[
  { "id": "uuid", "name": "シルバー" },
  { "id": "uuid", "name": "白" }
]
```

---

### GET `/masters/coat-patterns` 🌐

模様マスター一覧を取得する。

**Response 200 OK**
```json
[
  { "id": "uuid", "name": "タビー（縞）" },
  { "id": "uuid", "name": "単色（ソリッド）" }
]
```

---

### GET `/masters/coat-lengths` 🌐

毛の長さマスター一覧を取得する。

**Response 200 OK**
```json
[
  { "id": "uuid", "name": "短毛" },
  { "id": "uuid", "name": "長毛" }
]
```

---

## クイズ API

### GET `/quiz/today` 🔒

今日の一匹のクイズ問題を取得する。ホーム画面で使用。

**Response 200 OK**
```json
{
  "question_type": "photo_to_name",
  "cat_id": "uuid",
  "photo_url": "https://cdn.example.com/cats/ame-short/1.jpg",
  "choices": [
    { "id": "uuid", "name": "アメリカンショートヘア" },
    { "id": "uuid", "name": "ブリティッシュショートヘア" },
    { "id": "uuid", "name": "スコティッシュフォールド" },
    { "id": "uuid", "name": "ロシアンブルー" }
  ]
}
```

**処理フロー**
- 日付（YYYY-MM-DD）＋ユーザーID をシードとして乱数生成
- 同一ユーザー・同一日付では常に同じ猫を返す
- 選択肢はランダムシャッフル（正解位置をランダムに）

**参照テーブル**：`cat_breeds`, `cat_photos`

---

### GET `/quiz/session` 🔒

クイズ全10問を一括生成して返す。クイズ画面の開始時に1回だけ呼び出す。

**Response 200 OK**
```json
{
  "session_id": "server-generated-uuid",
  "questions": [
    {
      "question_number": 1,
      "question_type": "photo_to_name",
      "cat_id": "uuid",
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
      "cat_id": "uuid",
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
2. `wrong_count` を重みとして10種の猫を**重複なし**で選択（誤答多いほど優先、足りない場合はランダム補完）
3. 各問題の出題形式（photo_to_name / name_to_photo）をランダム決定
4. 各問題の不正解選択肢3種をランダム選択
5. 全10問をまとめてレスポンス

**参照テーブル**：`wrong_answers`, `cat_breeds`, `cat_photos`

---

### POST `/quiz/answer` 🔒

クイズ回答を送信し、正誤判定結果を返す。クイズ画面（P002）・ホーム画面の今日の一匹（P001）の両方で使用。

**Request Body**
```json
{
  "source": "quiz",           // "quiz" | "today"
  "session_id": "server-generated-uuid",  // GET /quiz/session で返った ID（source="quiz" 時は必須）
  "question_number": 3,       // 問題番号（source="today" 時は省略可、デフォルト 1）
  "cat_id": "uuid",           // 正解の猫ID（GET /quiz/session または GET /quiz/today で返った cat_id）
  "selected_cat_id": "uuid"   // ユーザーが選んだ猫ID
}
```

**Validation**
| フィールド | ルール |
|-----------|--------|
| source | 必須・`"quiz"` または `"today"` |
| session_id | source="quiz" の場合は必須 |
| question_number | 1〜10の整数（source="today" の場合は省略可） |
| cat_id | 必須・存在する猫ID |
| selected_cat_id | 必須・存在する猫ID |

**Response 200 OK**
```json
{
  "is_correct": true,
  "correct_cat_id": "uuid"
}
```

**処理フロー**
- `cat_id == selected_cat_id` で正誤判定
- 不正解の場合：`wrong_answers` に UPSERT（`ON CONFLICT (user_id, cat_breed_id) DO UPDATE wrong_count += 1, last_wrong_at = NOW()`）
- 正解の場合：`correct_answers` に INSERT（`ON CONFLICT DO NOTHING`）

**副作用**：`wrong_answers` UPSERT（不正解時）/ `correct_answers` INSERT（正解時・重複なし）

---

## ユーザー統計 API

### GET `/users/me/stats` 🔒

ユーザーの累計統計を取得する。結果画面で使用。

**Response 200 OK**
```json
{
  "total_correct_breeds": 42
}
```

**処理フロー**：`COUNT(*) FROM correct_answers WHERE user_id = ?`

**参照テーブル**：`correct_answers`

---

### POST `/users/me/sessions` 🔒

10問完了後にセッション結果を保存する。解説画面の「次の問題へ（10問完了時）」で呼び出す。

**Request Body**
```json
{
  "source": "quiz",       // "quiz" | "today"
  "correct_count": 7,
  "incorrect_count": 3
}
```

**Validation**
| フィールド | ルール |
|-----------|--------|
| source | 必須・`"quiz"` または `"today"` |
| correct_count | 0以上の整数 |
| incorrect_count | 0以上の整数 |
| 合計チェック | source="quiz" の場合 correct_count + incorrect_count = 10、source="today" の場合 = 1 |

**Response 201 Created**
```json
{
  "id": "uuid",
  "correct_count": 7,
  "incorrect_count": 3,
  "correct_rate": 0.7,
  "completed_at": "2026-03-03T12:00:00Z"
}
```

**副作用**：`session_results` INSERT

---

### GET `/users/me/sessions/latest` 🔒

最新セッション結果を取得する。結果画面（P006）の表示に使用。

**Response 200 OK**
```json
{
  "id": "uuid",
  "correct_count": 7,
  "incorrect_count": 3,
  "correct_rate": 0.7,
  "completed_at": "2026-03-03T12:00:00Z"
}
```

**Response 404 Not Found**（セッション結果なし）
```json
{ "detail": "No session found" }
```

**参照テーブル**：`session_results`（ORDER BY completed_at DESC LIMIT 1）

---

## 共通エラーレスポンス

| ステータス | 意味 | 例 |
|-----------|------|-----|
| 400 | バリデーションエラー | メール形式不正・パスワード短い |
| 401 | 未認証 | Cookie なし / JWT 期限切れ |
| 403 | 権限なし | 他ユーザーのデータへのアクセス |
| 404 | リソース不存在 | 存在しない猫ID |
| 409 | 重複 | 登録済みメールアドレス |
| 422 | リクエスト形式エラー | FastAPI デフォルト |
| 500 | サーバーエラー | 予期せぬ例外 |

**エラーレスポンス形式**
```json
{ "detail": "エラーメッセージ" }
```

---

## API と画面の対応表

| 画面 | 使用する API |
|------|------------|
| P007 ログイン・登録 | `POST /auth/register`, `POST /auth/login`, `POST /auth/google` |
| P001 ホーム | `GET /auth/me`, `GET /quiz/today`, `POST /quiz/answer` |
| P002 クイズ | `GET /quiz/session`, `POST /quiz/answer` |
| P003 解説 | `GET /cat-breeds/{id}`, `GET /cat-breeds/{id}/similar`, `POST /users/me/sessions` |
| P004 猫図鑑 | `GET /cat-breeds`, `GET /masters/coat-colors`, `GET /masters/coat-patterns`, `GET /masters/coat-lengths` |
| P005 猫詳細 | `GET /cat-breeds/{id}` |
| P006 結果 | `GET /users/me/sessions/latest`, `GET /users/me/stats` |

---

## 補足事項

### Cookie 設定
```
Set-Cookie: access_token=<JWT>; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=86400
```

### CORS 設定
- `Access-Control-Allow-Origin`: Vercel ドメイン（本番・プレビュー）
- `Access-Control-Allow-Credentials: true`

### キャッシュ方針
| エンドポイント | キャッシュ |
|--------------|---------|
| `/cat-breeds*`, `/masters/*` | CloudFront キャッシュ可（静的マスターデータ） |
| `/quiz/*`, `/users/*` | キャッシュなし（ユーザー固有データ） |
| `/auth/*` | キャッシュなし |
