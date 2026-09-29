import os
from pathlib import Path


def test_project_env_path_is_root_relative():
    import src.ai.copilot as copilot
    assert (copilot.BASE_DIR / "app.py").exists()


def test_missing_local_secrets_do_not_raise(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    import src.ai.copilot as copilot
    assert isinstance(copilot.is_configured(), bool)
