"""Release-document checks (block 3.3 plan §2): links resolve, named make targets exist, cited IDs exist."""
from scripts.doc_check import check_document

MAKEFILE = "test: ## t\n\techo\nreport: ## r\n\techo\ntest-e2e: ## e\n\techo\n"
CONFLICTS = "| C57 | x | y | z | Resolved |\n| C72 | x | y | z | Resolved |\n"
EVAL_IDS = {"E1", "E6", "E14"}
ADRS = {"ADR-002", "ADR-003"}


def _check(text, tmp_path, name="README.md"):
    (tmp_path / "docs").mkdir(exist_ok=True)
    (tmp_path / "docs" / "real.md").write_text("x")
    doc = tmp_path / name
    doc.write_text(text)
    return check_document(doc, tmp_path, MAKEFILE, CONFLICTS, EVAL_IDS, ADRS)


def test_clean_document_has_no_problems(tmp_path):
    text = "See [the report](docs/real.md) and [site](https://example.com). Run `make test`, `make test-e2e` then `make report`. E6 failed (C57); ADR-002."
    assert _check(text, tmp_path) == []


def test_broken_link_is_reported(tmp_path):
    assert any("docs/missing.md" in p for p in _check("[x](docs/missing.md)", tmp_path))


def test_link_anchor_and_relative_path_from_a_subfolder(tmp_path):
    (tmp_path / "sub").mkdir()
    assert _check("[ok](../docs/real.md#part) [bad](../docs/nope.md)", tmp_path, "sub/note.md") == ["broken link: ../docs/nope.md"]


def test_unknown_make_target_is_reported(tmp_path):
    assert _check("Run `make deploy`.", tmp_path) == ["unknown make target: deploy"]


def test_unknown_ids_are_reported(tmp_path):
    problems = _check("C99 and E15 and ADR-099 and C72 and E14 and ADR-003.", tmp_path)
    assert sorted(problems) == ["unknown ADR: ADR-099", "unknown conflict: C99", "unknown evaluation: E15"]


def test_separate_code_spans_are_not_joined_into_a_command(tmp_path):
    assert _check("The tools provide `make` and `git`.", tmp_path) == []
