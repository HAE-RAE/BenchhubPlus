"""Pytest package configuration."""

import os

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("CORS_ALLOWED_ORIGINS", "[\"http://testserver\"]")

os.makedirs("logs", exist_ok=True)