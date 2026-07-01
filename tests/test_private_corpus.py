import json
import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "tests" / "private_corpus.toml"
SCRIPT_PATH = REPO_ROOT / "scripts" / "prepare_private_corpus.py"
PRIVATE_ROOT = REPO_ROOT / "tests" / "private"


def _combined_output(result):
    return f"{result.stdout}\n{result.stderr}"


def _run_corpus_cli(*args):
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *map(str, args)],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=30,
    )


def _write_synthetic_manifest(path, source_root):
    path.write_text(
        "\n".join(
            (
                "[sources.synthetic]",
                f"path = {json.dumps(str(source_root))}",
                'kind = "markdown"',
                'profiles = ["smoke"]',
                "",
                "[profiles.smoke]",
                "limit = 1",
                'patterns = ["*.md"]',
                "",
            )
        ),
        encoding="utf-8",
    )


def _write_synthetic_source(root):
    root.mkdir(parents=True)
    (root / "chapter.md").write_text(
        "# Synthetic public sample\n\nThis is not private corpus content.\n",
        encoding="utf-8",
    )


def _manifest_or_skip() -> Path:
    if not MANIFEST_PATH.is_file():
        pytest.skip("optional local private corpus manifest is not configured")
    return MANIFEST_PATH


def _assert_actionable_missing_source_diagnostic(output, missing_path):
    normalized = output.lower()
    assert str(missing_path).lower() in normalized
    assert any(
        marker in normalized
        for marker in ("missing", "not found", "unavailable", "does not exist")
    ), output
    assert "traceback" not in normalized


def test_private_corpus_manifest_exists_and_names_required_source_families():
    manifest_path = _manifest_or_skip()

    try:
        manifest = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        pytest.fail(f"private corpus manifest must be valid TOML: {exc}")

    sources = manifest.get("sources")
    profiles = manifest.get("profiles")
    assert isinstance(sources, dict) and sources, "Manifest must define [sources.*]."
    assert isinstance(profiles, dict) and profiles, "Manifest must define [profiles.*]."

    for name, config in sources.items():
        assert isinstance(config, dict), f"Source {name!r} must be a TOML table."
        assert any(key in config for key in ("path", "paths", "candidates")), (
            f"Source {name!r} must name at least one local path candidate."
        )


def test_prepare_private_corpus_script_exists_with_basic_cli_entrypoint():
    assert SCRIPT_PATH.is_file(), "M1 must add scripts/prepare_private_corpus.py."


def test_list_command_reports_manifest_sources_and_profiles():
    manifest_path = _manifest_or_skip()
    result = _run_corpus_cli("list", "--manifest", manifest_path)

    assert result.returncode == 0, _combined_output(result)
    output = _combined_output(result).lower()
    assert "sources:" in output
    assert "profiles:" in output
    assert "profile" in output or "smoke" in output
    assert "traceback" not in output


def test_check_command_reports_missing_sources_without_traceback(tmp_path):
    missing_source = tmp_path / "missing-source-root"
    manifest = tmp_path / "private_corpus.toml"
    _write_synthetic_manifest(manifest, missing_source)

    result = _run_corpus_cli("check", "--manifest", manifest, "--source", "synthetic")

    assert result.returncode != 0, _combined_output(result)
    _assert_actionable_missing_source_diagnostic(_combined_output(result), missing_source)


def test_prepare_command_writes_public_synthetic_sample_under_tests_private(tmp_path):
    source_root = tmp_path / "synthetic-source"
    manifest = tmp_path / "private_corpus.toml"
    output_root = PRIVATE_ROOT / "pytest-synthetic-corpus"
    _write_synthetic_source(source_root)
    _write_synthetic_manifest(manifest, source_root)

    if output_root.exists():
        shutil.rmtree(output_root)

    try:
        result = _run_corpus_cli(
            "prepare",
            "--manifest",
            manifest,
            "--source",
            "synthetic",
            "--profile",
            "smoke",
            "--out",
            output_root,
        )

        assert result.returncode == 0, _combined_output(result)
        assert output_root.is_dir()
        generated_files = [path for path in output_root.rglob("*") if path.is_file()]
        assert generated_files, "prepare must materialize at least one sample file."
        assert all(path.is_relative_to(PRIVATE_ROOT) for path in generated_files)
        assert "traceback" not in _combined_output(result).lower()
    finally:
        if output_root.exists():
            shutil.rmtree(output_root)


def test_prepare_rejects_output_outside_tests_private(tmp_path):
    source_root = tmp_path / "synthetic-source"
    manifest = tmp_path / "private_corpus.toml"
    unsafe_output = REPO_ROOT / "tests" / "fixtures" / "__private_corpus_probe__"
    _write_synthetic_source(source_root)
    _write_synthetic_manifest(manifest, source_root)
    assert not unsafe_output.exists(), f"Refusing to use existing path: {unsafe_output}"

    try:
        result = _run_corpus_cli(
            "prepare",
            "--manifest",
            manifest,
            "--source",
            "synthetic",
            "--profile",
            "smoke",
            "--out",
            unsafe_output,
        )

        assert result.returncode != 0, _combined_output(result)
        output = _combined_output(result).lower()
        assert "tests/private" in output or "ignored" in output
        assert "traceback" not in output
        assert not unsafe_output.exists()
    finally:
        if unsafe_output.exists():
            shutil.rmtree(unsafe_output)


def test_private_corpus_pytest_marker_is_registered(request):
    markers = request.config.getini("markers")
    assert any(marker.startswith("private_corpus:") for marker in markers), (
        "Register private_corpus in pytest config so private tests can be selected "
        "without PytestUnknownMarkWarning."
    )


@pytest.mark.private_corpus
def test_private_corpus_fixture_points_to_prepared_samples(private_corpus_root):
    corpus_root = Path(private_corpus_root)

    assert corpus_root.is_dir()
    assert corpus_root.is_relative_to(PRIVATE_ROOT) or "HYPOLATEX_TEST_CORPUS" in os.environ
    assert any(path.is_file() for path in corpus_root.rglob("*"))


def test_gitignore_ignores_private_corpus_and_results_paths():
    assert (REPO_ROOT / ".gitignore").is_file(), (
        "M1 must add .gitignore before private corpus generation is allowed."
    )

    ignored_paths = (
        "tests/private/corpus/sample.md",
        "tests/private/results/result.json",
        "tests/private/results/output.pdf",
        "tests/private/results/output.log",
    )
    for ignored_path in ignored_paths:
        result = subprocess.run(
            ["git", "check-ignore", "--quiet", ignored_path],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            timeout=10,
        )
        assert result.returncode == 0, f"{ignored_path} must be ignored by git."
