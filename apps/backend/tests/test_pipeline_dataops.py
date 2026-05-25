import importlib


def test_import_pipeline_main():
    mod = importlib.import_module("apps.backend.cli.pipeline_dataops")
    assert hasattr(mod, "main")


def test_env_variable(monkeypatch):
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "dummy.json")
    from apps.backend.cli.pipeline_dataops import main

    assert callable(main)
