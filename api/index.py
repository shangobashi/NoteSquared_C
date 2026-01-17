"""Vercel serverless entrypoint for the FastAPI app."""

import os
import sys

# Ensure the repository root is on the import path.
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.app.main import app  # noqa: E402

