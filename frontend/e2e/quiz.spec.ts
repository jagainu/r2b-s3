import { test, expect, type Page } from "@playwright/test";
import { generateTestUser, loginAs, registerAndLogin } from "./helpers/auth";

// ──────────────────────────────────────────────────
// 前提: beforeAll でユーザー1回登録 + beforeEach でログイン
// ──────────────────────────────────────────────────
test.describe("クイズフロー", () => {
  let testUser: { email: string; password: string; username: string };

  test.beforeAll(async ({ browser }) => {
    testUser = generateTestUser();
    // 別 context でユーザー登録のみ実施（Cookie は保存しない）
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    await registerAndLogin(page, testUser);
    await ctx.close();
  });

  // 各テストは新規 context なので毎回ログインが必要
  test.beforeEach(async ({ page }) => {
    await loginAs(page, testUser.email, testUser.password);
  });

  // ──────────────────────────────────────────────
  // ホーム画面
  // ──────────────────────────────────────────────
  test("ダッシュボード（ホーム）に「クイズを始める」ボタンが表示される", async ({
    page,
  }) => {
    await expect(page.getByRole("heading", { name: "ホーム" })).toBeVisible();
    await expect(
      page.getByRole("button", { name: "クイズを始める" }),
    ).toBeVisible();
  });

  // ──────────────────────────────────────────────
  // クイズ開始 → 第1問表示
  // ──────────────────────────────────────────────
  test("「クイズを始める」をクリックするとクイズ画面に遷移し、第1問が表示される", async ({
    page,
  }) => {
    await page.getByRole("button", { name: "クイズを始める" }).click();

    // クイズ画面に遷移
    await expect(page).toHaveURL(/\/quiz/);

    // 問題が読み込まれるまで待機
    await expect(page.getByText("1 / 10")).toBeVisible({ timeout: 15_000 });

    // 選択肢ボタンが少なくとも4つ表示される
    const choices = page
      .locator("button")
      .filter({ hasNotText: /クイズを始める|もう一度|図鑑へ|ホームへ/ });
    const count = await choices.count();
    expect(count).toBeGreaterThanOrEqual(4);
  });

  // ──────────────────────────────────────────────
  // 1問回答 → 解説画面
  // ──────────────────────────────────────────────
  test("選択肢を選ぶと解説画面に遷移する", async ({ page }) => {
    await startQuizAndGetToQuestion(page);

    // 最初の選択肢をクリック
    await clickFirstChoice(page);

    // 解説画面に遷移
    await expect(page).toHaveURL(/\/quiz\/explanation/, { timeout: 15_000 });

    // 正解または不正解の表示
    await expect(page.getByText(/正解|不正解/).first()).toBeVisible({
      timeout: 10_000,
    });

    // 「次の問題へ」ボタンが表示される
    await expect(
      page.getByRole("button", { name: /次の問題へ|結果を見る/ }),
    ).toBeVisible();
  });

  // ──────────────────────────────────────────────
  // 「次の問題へ」で次問に進む
  // ──────────────────────────────────────────────
  test("解説画面で「次の問題へ」をクリックすると次の問題に進む", async ({
    page,
  }) => {
    await startQuizAndGetToQuestion(page);
    await clickFirstChoice(page);

    // 解説画面
    await expect(page).toHaveURL(/\/quiz\/explanation/, { timeout: 15_000 });
    await page.getByRole("button", { name: "次の問題へ" }).click();

    // 第2問に進む
    await expect(page).toHaveURL(/\/quiz/);
    await expect(page.getByText("2 / 10")).toBeVisible({ timeout: 15_000 });
  });

  // ──────────────────────────────────────────────
  // 全10問回答 → 結果画面
  // ──────────────────────────────────────────────
  test("10問すべてに回答すると結果画面に遷移し正答率が表示される", async ({
    page,
  }) => {
    await page.getByRole("button", { name: "クイズを始める" }).click();
    await expect(page).toHaveURL(/\/quiz/);

    // 10問ループして回答
    for (let i = 1; i <= 10; i++) {
      // 問題が表示されるまで待機
      await expect(page.getByText(`${i} / 10`)).toBeVisible({
        timeout: 15_000,
      });

      // 最初の選択肢を選ぶ
      await clickFirstChoice(page);

      // 解説画面に遷移
      await expect(page).toHaveURL(/\/quiz\/explanation/, { timeout: 15_000 });

      if (i < 10) {
        // 次の問題へ
        await page.getByRole("button", { name: "次の問題へ" }).click();
        await expect(page).toHaveURL(/\/quiz/);
      } else {
        // 最終問題 → 「結果を見る」
        await page.getByRole("button", { name: "結果を見る" }).click();
      }
    }

    // 結果画面
    await expect(page).toHaveURL(/\/quiz\/result/, { timeout: 15_000 });

    // 正答率が表示される（0%〜100%）
    await expect(page.getByText("正答率")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText(/%/)).toBeVisible();

    // 正解数・不正解数が表示される（exact: true で "不正解" と区別）
    await expect(page.getByText("正解", { exact: true })).toBeVisible();
    await expect(page.getByText("不正解", { exact: true })).toBeVisible();

    // 「もう一度挑戦」ボタン
    await expect(
      page.getByRole("button", { name: "もう一度挑戦" }),
    ).toBeVisible();
  });

  // ──────────────────────────────────────────────
  // 結果画面から「もう一度挑戦」でホームへ戻る
  // ──────────────────────────────────────────────
  test("結果画面の「もう一度挑戦」ボタンでダッシュボードへ戻る", async ({
    page,
  }) => {
    // クイズを1周完了
    await completeFullQuiz(page);

    // 「もう一度挑戦」クリック
    await page.getByRole("button", { name: "もう一度挑戦" }).click();
    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.getByRole("heading", { name: "ホーム" })).toBeVisible();
  });
});

// ──────────────────────────────────────────────────
// ヘルパー関数
// ──────────────────────────────────────────────────

/** クイズを開始して第1問の画面まで遷移する（beforeEach でダッシュボードにいる前提） */
async function startQuizAndGetToQuestion(page: Page) {
  await page.getByRole("button", { name: "クイズを始める" }).click();
  await expect(page).toHaveURL(/\/quiz/);
  await expect(page.getByText("1 / 10")).toBeVisible({ timeout: 15_000 });
}

/** クイズ画面で最初に表示された選択肢をクリックする */
async function clickFirstChoice(page: Page) {
  // 選択肢ボタン: テキストまたは画像を含むボタン
  // 「クイズを始める」「ホーム」等のナビゲーションボタンを除外
  const choiceButtons = page.locator("button:not([disabled])").filter({
    hasNotText: /クイズを始める|もう一度|図鑑へ|ホームへ/,
  });
  await choiceButtons.first().click({ timeout: 10_000 });
}

/** クイズを10問分すべて完了して結果画面まで遷移する（beforeEach でダッシュボードにいる前提） */
async function completeFullQuiz(page: Page) {
  await page.getByRole("button", { name: "クイズを始める" }).click();
  await expect(page).toHaveURL(/\/quiz/);

  for (let i = 1; i <= 10; i++) {
    await expect(page.getByText(`${i} / 10`)).toBeVisible({ timeout: 15_000 });
    await clickFirstChoice(page);
    await expect(page).toHaveURL(/\/quiz\/explanation/, { timeout: 15_000 });

    if (i < 10) {
      await page.getByRole("button", { name: "次の問題へ" }).click();
      await expect(page).toHaveURL(/\/quiz/);
    } else {
      await page.getByRole("button", { name: "結果を見る" }).click();
    }
  }

  await expect(page).toHaveURL(/\/quiz\/result/, { timeout: 15_000 });
}
