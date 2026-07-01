import json
import os
import stat
from pathlib import Path

import pytest
from typer.testing import CliRunner


TEST_ROOT = Path(__file__).parent
DOCTOR_FIXTURE_ROOT = TEST_ROOT / "fixtures" / "doctor"
DOCTOR_SNAPSHOT_ROOT = TEST_ROOT / "snapshots" / "doctor"
PRIVATE_CORPUS_ENV = "HYPOLATEX_TEST_CORPUS"


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "slow: required validation tests that exercise full external fixtures.",
    )
    config.addinivalue_line(
        "markers",
        "private_corpus: tests that require a local private corpus prepared under tests/private/.",
    )


@pytest.fixture(scope="session")
def private_corpus_root():
    configured = os.environ.get(PRIVATE_CORPUS_ENV)
    if not configured:
        pytest.skip(f"{PRIVATE_CORPUS_ENV} is not set")

    corpus_root = Path(configured).expanduser()
    if not corpus_root.is_absolute():
        corpus_root = (Path.cwd() / corpus_root).resolve(strict=False)

    if not corpus_root.exists():
        pytest.skip(f"{PRIVATE_CORPUS_ENV} does not exist: {corpus_root}")
    if not corpus_root.is_dir():
        pytest.skip(f"{PRIVATE_CORPUS_ENV} is not a directory: {corpus_root}")
    if not any(path.is_file() for path in corpus_root.rglob("*")):
        pytest.skip(f"{PRIVATE_CORPUS_ENV} contains no sample files: {corpus_root}")

    return corpus_root


def _required_toolchain():
    with (DOCTOR_FIXTURE_ROOT / "required_toolchain.json").open(
        encoding="utf-8"
    ) as fixture_file:
        return json.load(fixture_file)


@pytest.fixture(scope="session")
def required_executables():
    return tuple(_required_toolchain()["executables"])


@pytest.fixture(scope="session")
def required_tex_packages():
    return tuple(_required_toolchain()["tex_packages"])


@pytest.fixture(scope="session")
def doctor_ok_fragments():
    snapshot_file = DOCTOR_SNAPSHOT_ROOT / "doctor-ok-fragments.txt"
    return tuple(
        line.strip()
        for line in snapshot_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    )


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def cli_app():
    try:
        from hypolatex.cli import app
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Expected an importable Typer app at hypolatex.cli:app for M1 CLI tests. "
            f"Import failed: {exc}",
            pytrace=False,
        )
    return app


class FakeToolchain:
    def __init__(self, bin_dir):
        self.bin_dir = bin_dir

    def env(self, missing_tex_packages=(), missing_fonts=()):
        return {
            "PATH": str(self.bin_dir),
            "HYPOLATEX_FAKE_MISSING_TEX_PACKAGES": ",".join(missing_tex_packages),
            "HYPOLATEX_FAKE_MISSING_FONTS": ",".join(missing_fonts),
        }


@pytest.fixture
def fake_toolchain_factory(tmp_path, required_executables):
    def factory(missing_executables=()):
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        missing = set(missing_executables)
        for executable in required_executables:
            if executable in missing:
                continue
            _write_fake_executable(bin_dir / executable, executable)
        return FakeToolchain(bin_dir)

    return factory


def _write_fake_executable(path, executable):
    if executable == "kpsewhich":
        script = """#!/bin/sh
target=""
for arg in "$@"; do
  target="$arg"
done
target="${target##*/}"
package="${target%.sty}"
case ",${HYPOLATEX_FAKE_MISSING_TEX_PACKAGES}," in
  *,"${package}",*)
    printf 'not found: %s\\n' "$target" >&2
    exit 1
    ;;
esac
printf '/fake/texmf/tex/latex/%s/%s.sty\\n' "$package" "$package"
"""
    elif executable == "python3":
        script = """#!/bin/sh
printf 'Python 3.12.0\\n'
"""
    elif executable == "fc-match":
        script = """#!/bin/sh
target=""
for arg in "$@"; do
  case "$arg" in
    -*)
      ;;
    *)
      target="$arg"
      ;;
  esac
done
case ",${HYPOLATEX_FAKE_MISSING_FONTS}," in
  *,"${target}",*)
    printf 'DejaVu Sans\\n'
    exit 0
    ;;
esac
printf '%s\\n' "$target"
"""
    else:
        script = f"""#!/bin/sh
printf '{executable} 1.0.0\\n'
"""

    path.write_text(script, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
