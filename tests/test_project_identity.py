from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_project_metadata_uses_xfetch_identity():
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert 'name = "xfetch"' in pyproject
    assert 'description = "Chat-first link preservation runtime' in pyproject
    assert 'name: xfetch' in skill
    assert '# xfetch' in readme.splitlines()[0:5]
