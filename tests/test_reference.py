"""Bounded documentation/text tests; not a substitute for independent source review."""

import ast
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
MARKDOWN = [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md"))]


def slug(heading):
    return re.sub(r"[^\w\- ]", "", heading.lower()).strip().replace(" ", "-")


def test_local_markdown_links_anchors_and_assets_exist():
    checked = 0
    for document in MARKDOWN:
        for target in re.findall(r"!?\[[^\]]*\]\(([^\s)]+)\)", document.read_text()):
            parts = urlsplit(target)
            if parts.scheme or parts.netloc:
                continue  # Deliberately offline: no private data or link requests leave this test.
            path = (document.parent / unquote(parts.path)).resolve() if parts.path else document
            assert path == ROOT or ROOT in path.parents, (document, target)
            assert path.exists(), (document.relative_to(ROOT), target)
            if parts.fragment and path.suffix == ".md":
                headings = re.findall(r"^#{1,6}\s+(.+)$", path.read_text(), flags=re.MULTILINE)
                assert unquote(parts.fragment) in {slug(heading) for heading in headings}, target
            checked += 1
    assert checked > 25


def test_named_python_test_references_are_real():
    names = {
        node.name
        for path in (ROOT / "tests").glob("test_*.py")
        for node in ast.walk(ast.parse(path.read_text()))
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
    }
    referenced = set()
    for document in MARKDOWN:
        referenced.update(re.findall(r"`(test_[A-Za-z0-9_]+)`", document.read_text()))
    assert len(referenced) >= 15
    assert referenced <= names, sorted(referenced - names)


def test_company_entrypoint_consolidates_roles_design_and_interview():
    reference = ROOT / "docs/company-reference.md"
    assert reference.is_file(), "Missing single start-here company reference"
    text = reference.read_text()
    for section in [
        "QA",
        "Engineering",
        "Operations",
        "Product",
        "Glossary",
        "SOLID",
        "Two-minute",
        "Requirements",
    ]:
        assert section in text
    assert "docs/company-reference.md" in (ROOT / "README.md").read_text()
    assert not (ROOT / "docs/walkthrough.md").exists(), (
        "Obsolete parallel walkthrough is duplicated"
    )


def test_documented_resolution_command_has_real_help_and_no_embedded_program():
    result = subprocess.run(
        [sys.executable, "-m", "scripts.resolve_questions", "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert "--runtime" in result.stdout and "--port" in result.stdout
    demo = (ROOT / "docs/demo.md").read_text()
    assert "python -m scripts.resolve_questions" in demo
    assert "def call(" not in demo, "The executable example should have one maintained home"


def test_public_reference_keeps_demo_qualification_and_operations_boundaries():
    reference = ROOT / "docs/company-reference.md"
    assert reference.exists()
    text = reference.read_text()
    for phrase in [
        "SYNTHETIC",
        "UNKNOWN",
        "not production",
        "not a professional signature",
        "independent",
        "no external",
    ]:
        assert phrase in text
    assert "127.0.0.1:8174" in text
    assert "UI dom-reset-v3" in text
