"""Export the FastAPI app's OpenAPI schema to openapi.json.

Usage:
    python scripts/export_openapi.py

No running server is required; this imports the FastAPI app object directly
and serializes app.openapi().
"""
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.main import app  # noqa: E402

OUTPUT_PATH = PROJECT_ROOT / "openapi.json"


def main() -> None:
    schema = app.openapi()
    OUTPUT_PATH.write_text(
        json.dumps(schema, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Wrote OpenAPI schema to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
