from __future__ import annotations

import hashlib
import os
from pathlib import Path
import shlex
import shutil
import stat
import subprocess
import sys
import textwrap

import pytest


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "scripts" / "install.sh"
REVISION = "fixture-revision"


def _copy_fixture_source(destination: Path) -> Path:
    """Build a small source tree whose path also exercises shell quoting."""

    destination.mkdir(parents=True)
    for name in ("pyproject.toml", "SKILL.md", "README.md", "VERSION"):
        shutil.copy2(ROOT / name, destination / name)
    shutil.copytree(ROOT / "xfetch", destination / "xfetch")
    return destination


def _write_fake_uv(bin_dir: Path) -> Path:
    """Provide deterministic uv operations for installer file-layout tests.

    These tests intentionally exercise the installer's transaction and path
    handling without downloading Python or packages. A separate manual test
    covers the real uv bootstrap path.
    """

    bin_dir.mkdir(parents=True)
    uv = bin_dir / "uv"
    uv.write_text(
        textwrap.dedent(
            f"""\
            #!{sys.executable}
            from pathlib import Path
            import os
            import shlex
            import subprocess
            import sys

            args = sys.argv[1:]
            log_path = os.environ.get("XFETCH_FAKE_UV_LOG")
            if log_path:
                with Path(log_path).open("a", encoding="utf-8") as log:
                    log.write(repr(args) + "\\n")
            if args == ["--version"]:
                print("uv fixture 0.0")
                raise SystemExit(0)

            if args[:2] == ["python", "install"]:
                raise SystemExit(0)

            if args[:2] == ["python", "find"]:
                print({sys.executable!r})
                raise SystemExit(0)

            if args and args[0] == "venv":
                target = Path(args[-1])
                subprocess.run([{sys.executable!r}, "-m", "venv", str(target)], check=True)
                raise SystemExit(0)

            if args and args[0] == "pip":
                if os.environ.get("XFETCH_FAKE_UV_FAIL") == "1":
                    raise SystemExit(73)
                try:
                    py = args[args.index("--python") + 1]
                except (ValueError, IndexError):
                    print("fixture uv expected --python", file=sys.stderr)
                    raise SystemExit(74)
                source = next(
                    (
                        Path(item)
                        for item in reversed(args[1:])
                        if not item.startswith("-") and Path(item).is_dir()
                    ),
                    None,
                )
                if source is None:
                    print("fixture uv expected a source directory", file=sys.stderr)
                    raise SystemExit(75)
                executable = Path(py).parent / "xfetch"
                executable.write_text(
                    "#!/bin/sh\\n"
                    + "'''exec' " + shlex.quote(py) + " \\\"$0\\\" \\\"$@\\\"\\n"
                    + "' '''\\n"
                    + "import sys\\n"
                    + "sys.path.insert(0, " + repr(str(source)) + ")\\n"
                    + "from xfetch.cli import main\\n"
                    + "raise SystemExit(main())\\n"
                )
                executable.chmod(executable.stat().st_mode | 0o111)
                raise SystemExit(0)

            print("fixture uv unsupported command: " + " ".join(args), file=sys.stderr)
            raise SystemExit(76)
            """
        ),
        encoding="utf-8",
    )
    uv.chmod(uv.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return uv


def _environment(home: Path, fake_bin: Path) -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(
        {
            "HOME": str(home),
            "XDG_CONFIG_HOME": str(home / ".config"),
            "XDG_CACHE_HOME": str(home / ".cache"),
            "UV_CACHE_DIR": str(home / ".cache" / "uv"),
            "UV_PYTHON_INSTALL_DIR": str(home / ".local" / "share" / "uv" / "python"),
            "PATH": f"{fake_bin}:/usr/bin:/bin",
        }
    )
    for key in ("VIRTUAL_ENV", "XFETCH_FAKE_UV_FAIL", "XFETCH_FAKE_UV_LOG"):
        environment.pop(key, None)
    return environment


def _run_install(
    tmp_path: Path,
    agent: str,
    *,
    revision: str = REVISION,
    source_dir: Path | None = None,
    fail_uv: bool = False,
) -> tuple[subprocess.CompletedProcess[str], Path, Path]:
    if not INSTALLER.is_file():
        pytest.fail(f"installer is missing: {INSTALLER}")

    home = tmp_path / "home with spaces"
    home.mkdir(parents=True, exist_ok=True)
    fake_bin = tmp_path / "fake bin"
    _write_fake_uv(fake_bin)
    source = source_dir or _copy_fixture_source(tmp_path / "source with spaces")
    environment = _environment(home, fake_bin)
    (tmp_path / "unrelated cwd").mkdir(parents=True, exist_ok=True)
    if fail_uv:
        environment["XFETCH_FAKE_UV_FAIL"] = "1"
    command = [
        "sh",
        str(INSTALLER),
        "--agent",
        agent,
        "--source-dir",
        str(source),
        "--revision",
        revision,
    ]
    result = subprocess.run(
        command,
        cwd=tmp_path / "unrelated cwd",
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return result, home, source


def _run_install_into_home(
    tmp_path: Path,
    home: Path,
    source: Path,
    agent: str,
    revision: str = REVISION,
    uv_log: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    fake_bin = tmp_path / "repeat fake bin"
    _write_fake_uv(fake_bin)
    environment = _environment(home, fake_bin)
    if uv_log is not None:
        environment["XFETCH_FAKE_UV_LOG"] = str(uv_log)
    cwd = tmp_path / "repeat unrelated cwd"
    cwd.mkdir(parents=True, exist_ok=True)
    return subprocess.run(
        [
            "sh",
            str(INSTALLER),
            "--agent",
            agent,
            "--source-dir",
            str(source),
            "--revision",
            revision,
        ],
        cwd=cwd,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def _tree_digest(root: Path) -> dict[str, str]:
    if not root.exists():
        return {}
    digest: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            digest[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest


@pytest.mark.parametrize(
    ("agent", "skill_roots"),
    [
        ("codex", (".agents/skills/xfetch",)),
        ("claude", (".claude/skills/xfetch",)),
        ("both", (".agents/skills/xfetch", ".claude/skills/xfetch")),
    ],
)
def test_installs_each_agent_mode_with_isolated_absolute_runtime(tmp_path, agent, skill_roots):
    profile_contents = {
        ".profile": "profile sentinel\n",
        ".bashrc": "bashrc sentinel\n",
        ".zshrc": "zshrc sentinel\n",
        ".zshenv": "zshenv sentinel\n",
    }
    home = tmp_path / "home with spaces"
    home.mkdir(parents=True)
    for name, content in profile_contents.items():
        (home / name).write_text(content, encoding="utf-8")
    result, home, source = _run_install(tmp_path, agent)
    assert result.returncode == 0, result.stdout

    runtime_root = home / ".local" / "share" / "xfetch"
    executable = runtime_root / "venv" / "bin" / "xfetch"
    assert executable.is_file()
    assert executable.stat().st_mode & stat.S_IXUSR
    assert not (home / "xfetch-content").exists()

    for relative_root in skill_roots:
        skill_root = home / relative_root
        assert (skill_root / "SKILL.md").is_file()
        reference = skill_root / "INSTALLATION.md"
        assert reference.is_file()
        content = reference.read_text(encoding="utf-8")
        assert REVISION in content
        assert str(executable) in content
        assert "xfetch-content" in content
        assert (skill_root / ".xfetch-managed").is_file()

    # The generated entry point must work from an unrelated directory with
    # no activated environment and no user-local bin directory on PATH.
    invocation_environment = _environment(home, tmp_path / "empty bin")
    invocation_environment["PATH"] = "/usr/bin:/bin"
    invocation = subprocess.run(
        [str(executable), "--help"],
        cwd=tmp_path / "unrelated cwd",
        env=invocation_environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    assert invocation.returncode == 0, invocation.stdout
    assert "usage:" in invocation.stdout

    # The installer must not modify shell startup files as a side effect.
    for name, content in profile_contents.items():
        assert not (home / name).exists() or (home / name).read_text(encoding="utf-8") == content

    # The installed runtime must come from the requested source tree.
    assert source.name == "source with spaces"


def test_reinstalling_identical_source_is_a_noop(tmp_path):
    first, home, source = _run_install(tmp_path, "codex")
    assert first.returncode == 0, first.stdout
    before = _tree_digest(home)

    second, second_home, _ = _run_install(
        tmp_path / "second",
        "codex",
        source_dir=source,
    )
    assert second.returncode == 0, second.stdout
    # The second invocation uses a fresh HOME above; repeat in the original
    # HOME to assert that an identical managed installation is not rewritten.
    uv_log = tmp_path / "repeat uv.log"
    repeated = _run_install_into_home(
        tmp_path, home, source, "codex", uv_log=uv_log
    )
    assert repeated.returncode == 0, repeated.stdout
    assert _tree_digest(home) == before
    calls = uv_log.read_text(encoding="utf-8").splitlines() if uv_log.exists() else []
    assert not any("'venv'" in call or "'pip'" in call for call in calls)
    assert second_home.exists()


def test_second_host_reuses_identical_managed_runtime(tmp_path):
    first, home, source = _run_install(tmp_path, "codex")
    assert first.returncode == 0, first.stdout
    runtime = home / ".local" / "share" / "xfetch"
    before = _tree_digest(runtime)

    uv_log = tmp_path / "second host uv.log"
    second = _run_install_into_home(
        tmp_path, home, source, "claude", uv_log=uv_log
    )
    assert second.returncode == 0, second.stdout
    assert _tree_digest(runtime) == before
    calls = uv_log.read_text(encoding="utf-8").splitlines() if uv_log.exists() else []
    assert not any("'venv'" in call or "'pip'" in call for call in calls)
    assert (home / ".agents" / "skills" / "xfetch" / "SKILL.md").is_file()
    assert (home / ".claude" / "skills" / "xfetch" / "SKILL.md").is_file()


def test_modified_managed_runtime_entrypoint_is_preserved(tmp_path):
    first, home, source = _run_install(tmp_path, "codex")
    assert first.returncode == 0, first.stdout
    executable = home / ".local" / "share" / "xfetch" / "venv" / "bin" / "xfetch"
    executable.write_text("#!/bin/sh\necho user-edit\n", encoding="utf-8")
    executable.chmod(0o755)
    before = executable.read_bytes()

    result = _run_install_into_home(tmp_path, home, source, "codex")
    assert result.returncode != 0, result.stdout
    assert executable.read_bytes() == before


def test_missing_managed_runtime_executable_stops_without_uv_or_deletion(tmp_path):
    first, home, source = _run_install(tmp_path, "codex")
    assert first.returncode == 0, first.stdout
    runtime = home / ".local" / "share" / "xfetch"
    executable = runtime / "venv" / "bin" / "xfetch"
    executable.unlink()
    uv_log = tmp_path / "missing executable uv.log"

    result = _run_install_into_home(
        tmp_path, home, source, "codex", uv_log=uv_log
    )
    assert result.returncode != 0, result.stdout
    assert runtime.is_dir()
    assert (runtime / ".xfetch-runtime").is_file()
    assert not executable.exists()
    calls = uv_log.read_text(encoding="utf-8").splitlines() if uv_log.exists() else []
    assert not calls


def test_other_host_revision_conflict_is_rejected_before_mutation(tmp_path):
    first, home, source = _run_install(
        tmp_path, "codex", revision="revision-a"
    )
    assert first.returncode == 0, first.stdout
    runtime = home / ".local" / "share" / "xfetch"
    before = _tree_digest(runtime)

    result = _run_install_into_home(
        tmp_path, home, source, "claude", revision="revision-b"
    )
    assert result.returncode != 0, result.stdout
    assert _tree_digest(runtime) == before
    installed = home / ".agents" / "skills" / "xfetch" / "INSTALLATION.md"
    assert "revision-a" in installed.read_text(encoding="utf-8")
    assert not (home / ".claude" / "skills" / "xfetch").exists()


def test_unowned_runtime_conflict_is_rejected_before_mutation(tmp_path):
    home = tmp_path / "home with spaces"
    runtime_root = home / ".local" / "share" / "xfetch"
    runtime_root.mkdir(parents=True)
    sentinel = runtime_root / "keep-me.txt"
    sentinel.write_text("user data\n", encoding="utf-8")

    result, _, _ = _run_install(tmp_path, "codex")
    assert result.returncode != 0
    assert sentinel.read_text(encoding="utf-8") == "user data\n"
    assert not (home / ".agents" / "skills" / "xfetch").exists()


def test_modified_managed_skill_conflict_is_preserved(tmp_path):
    home = tmp_path / "home with spaces"
    skill_root = home / ".agents" / "skills" / "xfetch"
    skill_root.mkdir(parents=True)
    (skill_root / ".xfetch-managed").write_text(
        "xfetch-installer-managed-v1\n", encoding="utf-8"
    )
    skill = skill_root / "SKILL.md"
    skill.write_text("user edited skill\n", encoding="utf-8")
    reference = skill_root / "INSTALLATION.md"
    reference.write_text("user reference\n", encoding="utf-8")

    result, _, _ = _run_install(tmp_path, "codex")
    assert result.returncode != 0
    assert skill.read_text(encoding="utf-8") == "user edited skill\n"
    assert reference.read_text(encoding="utf-8") == "user reference\n"
    assert not (home / ".local" / "share" / "xfetch").exists()


@pytest.mark.parametrize(
    "arguments",
    [
        ("--agent", "bogus"),
        ("--agent", "codex", "--source-dir", "relative-source", "--revision", REVISION),
        ("--agent", "codex", "--source-dir", "/definitely/missing", "--revision", REVISION),
        ("--agent", "codex", "--source-dir", "."),
    ],
)
def test_invalid_inputs_fail_without_installation(tmp_path, arguments):
    assert INSTALLER.is_file(), f"installer is missing: {INSTALLER}"
    home = tmp_path / "home with spaces"
    environment = _environment(home, tmp_path / "fake bin")
    command = ["sh", str(INSTALLER), *arguments]
    result = subprocess.run(
        command,
        cwd=tmp_path,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    assert result.returncode != 0, result.stdout
    assert not (home / ".local" / "share" / "xfetch").exists()
    assert not (home / ".agents" / "skills" / "xfetch").exists()
    assert not (home / ".claude" / "skills" / "xfetch").exists()


def test_runtime_setup_failure_does_not_overwrite_unrelated_home_files(tmp_path):
    unrelated = tmp_path / "home with spaces" / "keep.txt"
    unrelated.parent.mkdir(parents=True)
    unrelated.write_text("preserve me\n", encoding="utf-8")

    result, home, _ = _run_install(tmp_path, "codex", fail_uv=True)
    assert result.returncode != 0
    assert unrelated.read_text(encoding="utf-8") == "preserve me\n"
    assert not (home / ".agents" / "skills" / "xfetch").exists()
