import type { Browser, Page } from "@playwright/test";

/** テスト用ユーザー（毎回ユニークなメールを使う） */
export function generateTestUser() {
  const ts = Date.now();
  return {
    email: `test-${ts}@example.com`,
    password: "Password123",
    username: `testuser${ts}`.slice(0, 20),
  };
}

/** ログインページからメール+パスワードでログインし、ダッシュボードまで遷移する */
export async function loginAs(
  page: Page,
  email: string,
  password: string,
): Promise<void> {
  await page.goto("/login");
  await page.getByLabel("メールアドレス").fill(email);
  await page.getByLabel("パスワード").fill(password);
  // "ログイン"ボタン（exact: true で "Google でログイン" と区別）
  await page.getByRole("button", { name: "ログイン", exact: true }).click();
  await page.waitForURL("**/dashboard");
}

/** 新規登録して自動ログイン状態にする */
export async function registerAndLogin(
  page: Page,
  user: { email: string; password: string; username: string },
): Promise<void> {
  await page.goto("/login");
  await page.getByRole("tab", { name: "新規登録" }).click();
  await page.getByLabel("ユーザー名").fill(user.username);
  await page.getByLabel("メールアドレス").fill(user.email);
  await page.getByLabel("パスワード").fill(user.password);
  await page.getByRole("button", { name: "新規登録", exact: true }).click();
  await page.waitForURL("**/dashboard");
}

/**
 * 新規ユーザーを登録して Cookie 状態を保存する。
 * quiz.spec.ts の beforeAll で使用し、各テストで Cookie を使い回す。
 */
export async function setupAuthState(
  browser: Browser,
  user: { email: string; password: string; username: string },
  storageStatePath: string,
): Promise<void> {
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  await registerAndLogin(page, user);
  await ctx.storageState({ path: storageStatePath });
  await ctx.close();
}
