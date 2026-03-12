export default {
  api: {
    input: {
      // openapi.json はプロジェクトルートに生成される（backend/scripts/export_openapi.py で出力）
      target: "./openapi.json",
    },
    output: {
      target: "./src/shared/api/generated/index.ts",
      // fetch クライアント + customInstance mutator で CSRF・Cookie 対応
      client: "fetch",
      mutator: {
        path: "./src/shared/api/mutator.ts",
        name: "customInstance",
      },
      clean: true,
      prettier: true,
    },
  },
};
