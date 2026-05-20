import pytest
import importlib

def test_import_pipeline_main():
    mod = importlib.import_module('pipeline_dataops')
    assert hasattr(mod, 'main')

def test_env_variable(monkeypatch):
    monkeypatch.setenv('GOOGLE_APPLICATION_CREDENTIALS', 'dummy.json')
    from pipeline_dataops import main
    assert callable(main)

# Dummy test to always pass
def test_sanity():
    assert 1 == 1
