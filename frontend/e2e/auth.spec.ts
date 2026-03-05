import { test, expect } from "@playwright/test";
import { generateTestUser, loginAs, registerAndLogin } from "./helpers/auth";

// ──────────────────────────────────────────────────
// 未認証リダイレクト
// ──────────────────────────────────────────────────
test.describe("未認証アクセス", () => {
  test("認証が必要なページにアクセスするとログイン画面へリダイレクトされる", async ({
    page,
  }) => {
    await page.goto("/dashboard");
    await expect(page).toHaveURL(/\/login/);
  });
});

// ──────────────────────────────────────────────────
// 新規登録
// ──────────────────────────────────────────────────
test.describe("新規登録", () => {
  test("正常登録 → ダッシュボードへ遷移", async ({ page }) => {
    const user = generateTestUser();
    await registerAndLogin(page, user);

    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.getByRole("heading", { name: "ホーム" })).toBeVisible();
  });

  test("フォームバリデーション: 空入力でエラーメッセージ表示", async ({
    page,
  }) => {
    await page.goto("/login");
    await page.getByRole("tab", { name: "新規登録" }).click();
    await page.getByRole("button", { name: "新規登録", exact: true }).click();

    await expect(page.getByText("ユーザー名を入力してください")).toBeVisible();
    await expect(page.getByText("メールアドレスを入力してください")).toBeVisible();
    await expect(page.getByText("パスワードを入力してください")).toBeVisible();
  });

  test("パスワードが8文字未満でエラー", async ({ page }) => {
    await page.goto("/login");
    await page.getByRole("tab", { name: "新規登録" }).click();

    await page.getByLabel("ユーザー名").fill("testuser");
    await page.getByLabel("メールアドレス").fill("test@example.com");
    await page.getByLabel("パスワード").fill("short");
    await page.getByRole("button", { name: "新規登録", exact: true }).click();

    await expect(page.getByText("パスワードは8文字以上で入力してください")).toBeVisible();
  });

  test("重複メールアドレスでAPIエラーが表示される", async ({ page }) => {
    const user = generateTestUser();
    await registerAndLogin(page, user);

    // 同じメールアドレスで再度登録試行
    await page.goto("/login");
    await page.getByRole("tab", { name: "新規登録" }).click();

    await page.getByLabel("ユーザー名").fill(user.username);
    await page.getByLabel("メールアドレス").fill(user.email);
    await page.getByLabel("パスワード").fill(user.password);
    await page.getByRole("button", { name: "新規登録", exact: true }).click();

    await expect(page.getByRole("alert")).toBeVisible();
  });
});

// ──────────────────────────────────────────────────
// ログイン
// ──────────────────────────────────────────────────
test.describe("ログイン", () => {
  // 各テストで使う共有ユーザーを beforeAll で1回だけ登録
  let sharedUser: { email: string; password: string; username: string };

  test.beforeAll(async ({ browser }) => {
    sharedUser = generateTestUser();
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    await registerAndLogin(page, sharedUser);
    await ctx.close();
  });

  test("正常ログイン → ダッシュボードへ遷移", async ({ page }) => {
    // 各テストは新規コンテキストなので clearCookies 不要
    await loginAs(page, sharedUser.email, sharedUser.password);

    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.getByRole("heading", { name: "ホーム" })).toBeVisible();
  });

  test("フォームバリデーション: 空入力でエラーメッセージ表示", async ({
    page,
  }) => {
    await page.goto("/login");
    await page.getByRole("button", { name: "ログイン", exact: true }).click();

    await expect(page.getByText("メールアドレスを入力してください")).toBeVisible();
    await expect(page.getByText("パスワードを入力してください")).toBeVisible();
  });

  test("誤ったパスワードでエラーメッセージ表示", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel("メールアドレス").fill(sharedUser.email);
    await page.getByLabel("パスワード").fill("WrongPassword!");
    await page.getByRole("button", { name: "ログイン", exact: true }).click();

    await expect(page.getByRole("alert")).toBeVisible();
  });

  test("ログインフォームと新規登録フォームが切り替わる", async ({ page }) => {
    await page.goto("/login");

    // 初期状態: ログインボタンあり
    await expect(page.getByRole("button", { name: "ログイン", exact: true })).toBeVisible();

    // 「新規登録」タブクリック
    await page.getByRole("tab", { name: "新規登録" }).click();
    await expect(page.getByRole("button", { name: "新規登録", exact: true })).toBeVisible();
    await expect(page.getByLabel("ユーザー名")).toBeVisible();

    // 「ログイン」タブに戻る
    await page.getByRole("tab", { name: "ログイン" }).click();
    await expect(page.getByRole("button", { name: "ログイン", exact: true })).toBeVisible();
  });
});
