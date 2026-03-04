"""FastAPI app から openapi.json をプロジェクトルートに出力するスクリプト。

Usage:
    cd backend/
    uv run python scripts/export_openapi.py
"""

import json
import sys
from pathlib import Path

# backend/ を Python パスに追加（app パッケージを import できるように）
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app  # noqa: E402

OUTPUT_PATH = Path(__file__).parent.parent.parent / "openapi.json"


def main() -> None:
    schema = app.openapi()
    OUTPUT_PATH.write_text(json.dumps(schema, ensure_ascii=False, indent=2))
    print(f"openapi.json を出力しました: {OUTPUT_PATH}")
    print(f"  エンドポイント数: {len(schema.get('paths', {}))}")


if __name__ == "__main__":
    main()
