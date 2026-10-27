import importlib.util


def test_smoke_import_nexus():
    """Smoke test: the package 'nexus' should be importable in the branch."""
    spec = importlib.util.find_spec('nexus')
    assert spec is not None, "Package 'nexus' not found; ensure package code is present in the branch"
