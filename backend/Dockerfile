# ─────────────────────────────────────────────────────────────
# Stage 1: builder
# uv で依存関係をインストール → venv を生成
# ─────────────────────────────────────────────────────────────
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

WORKDIR /app

# 依存関係定義のみ先にコピー（キャッシュ活用）
COPY pyproject.toml uv.lock ./

# 本番用依存のみインストール（--no-dev）
RUN uv sync --frozen --no-dev

# アプリコードをコピー
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./
COPY scripts/ ./scripts/

# ─────────────────────────────────────────────────────────────
# Stage 2: runtime
# venv のみコピーして軽量なイメージを作成
# ─────────────────────────────────────────────────────────────
FROM python:3.13-slim-bookworm AS runtime

# セキュリティ: 非 root ユーザーで実行
RUN groupadd --gid 1001 appgroup \
 && useradd --uid 1001 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# builder から venv とアプリを転送
COPY --from=builder --chown=appuser:appgroup /app/.venv /app/.venv
COPY --from=builder --chown=appuser:appgroup /app/app /app/app
COPY --from=builder --chown=appuser:appgroup /app/alembic /app/alembic
COPY --from=builder --chown=appuser:appgroup /app/alembic.ini /app/alembic.ini
COPY --from=builder --chown=appuser:appgroup /app/scripts /app/scripts

# venv の Python を使用
ENV PATH="/app/.venv/bin:$PATH"

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
