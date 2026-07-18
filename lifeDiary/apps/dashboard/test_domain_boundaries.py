import ast
from pathlib import Path

DASHBOARD_ROOT = Path(__file__).resolve().parent


def _imported_modules(source_path):
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            yield node.module


def test_dashboard_does_not_import_stats():
    """dashboard는 stats를 몰라야 한다. stats가 dashboard를 읽는 방향만 허용."""
    violations = []
    for source_path in DASHBOARD_ROOT.rglob("*.py"):
        if "__pycache__" in source_path.parts or source_path.name.startswith("test_"):
            continue
        for module in _imported_modules(source_path):
            if module == "apps.stats" or module.startswith("apps.stats."):
                violations.append(f"{source_path.relative_to(DASHBOARD_ROOT)} -> {module}")
    assert violations == []
