#!/usr/bin/env python3
"""Dump OpenAPI schema to JSON file. Run from backend dir: python scripts/dump_openapi.py"""
import json
import sys
from pathlib import Path

# Ensure app is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import app

if __name__ == "__main__":
    out_path = Path(__file__).resolve().parent.parent.parent / "frontend" / "openapi.json"
    schema = app.openapi()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(schema, f, indent=2)
    print(f"Wrote {out_path}")
