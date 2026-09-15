"""Documentation claims must track the implemented CLI and API."""

import ast
import re
from pathlib import Path


def _cli_option_strings() -> set[str]:
    tree = ast.parse(Path("src/web_similarity_audit/cli.py").read_text(encoding="utf-8"))
    return {
        value.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "add_argument"
        for value in node.args
        if isinstance(value, ast.Constant) and isinstance(value.value, str)
        and value.value.startswith("--")
    }


def test_readme_flags_are_cli_flags():
    flags = set(re.findall(r"(?<![\w-])(--[a-z][a-z-]+)", Path("README.md").read_text(encoding="utf-8")))
    assert flags - {"--help"} <= _cli_option_strings()


def test_docs_do_not_reference_removed_high_level_api():
    files = [Path("README.md"), *Path("docs").glob("*.md")]
    files = [path for path in files if path.name != "EXECUTION_PLAN_2026-09-15.md"]
    forbidden = ("from web_similarity_audit import Auditor", "--template-threshold")
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert not any(value in text for value in forbidden), path