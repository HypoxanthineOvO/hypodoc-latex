from pathlib import Path

import pytest


REQUIRED_CJK_FONTS = (
    "Noto Serif CJK SC",
    "Noto Sans CJK SC",
    "Noto Sans Mono CJK SC",
)

RECOMMENDED_CHINESE_FONTS = (
    "MiSans",
    "Sarasa Gothic SC",
    "LXGW WenKai",
    "LXGW WenKai Mono",
    "Smiley Sans",
    "Alibaba PuHuiTi 3.0",
    "DingTalk JinBuTi",
)

PDF_EVIDENCE_TOOLS = (
    "pdfinfo",
    "pdftotext",
    "pdftoppm",
)


def _normalized(output):
    return output.lower()


def _assert_actionable_failure(output):
    normalized = _normalized(output)
    assert any(
        marker in normalized
        for marker in ("missing", "not found", "unavailable", "install", "fail")
    ), output


def test_cli_root_help_lists_m1_command_surfaces(runner, cli_app):
    result = runner.invoke(cli_app, ["--help"])

    assert result.exit_code == 0, result.output
    help_output = _normalized(result.output)
    assert "doctor" in help_output
    assert "convert" in help_output
    assert "build" in help_output


def test_cli_subcommand_help_is_available(runner, cli_app):
    for command in ("doctor", "convert", "build"):
        result = runner.invoke(cli_app, [command, "--help"])

        assert result.exit_code == 0, result.output
        assert command in _normalized(result.output)


def test_doctor_reports_required_executables_when_available(
    runner,
    cli_app,
    fake_toolchain_factory,
    required_executables,
):
    fake_toolchain = fake_toolchain_factory()

    result = runner.invoke(cli_app, ["doctor"], env=fake_toolchain.env())

    assert result.exit_code == 0, result.output
    output = _normalized(result.output)
    for executable in required_executables:
        expected_fragment = "python" if executable == "python3" else executable
        assert expected_fragment in output


def test_doctor_reports_required_tex_packages_when_available(
    runner,
    cli_app,
    fake_toolchain_factory,
    required_tex_packages,
    doctor_ok_fragments,
):
    fake_toolchain = fake_toolchain_factory()

    result = runner.invoke(cli_app, ["doctor"], env=fake_toolchain.env())

    assert result.exit_code == 0, result.output
    output = _normalized(result.output)
    for package in required_tex_packages:
        assert package in output
    for fragment in doctor_ok_fragments:
        assert fragment in output


def test_doctor_reports_noto_cjk_fonts_and_poppler_tools_when_available(
    runner,
    cli_app,
    fake_toolchain_factory,
):
    fake_toolchain = fake_toolchain_factory()

    result = runner.invoke(cli_app, ["doctor"], env=fake_toolchain.env())

    assert result.exit_code == 0, result.output
    output = _normalized(result.output)
    assert "font" in output
    assert "poppler" in output or "pdf evidence" in output
    for font in REQUIRED_CJK_FONTS:
        assert font.lower() in output
    for font in RECOMMENDED_CHINESE_FONTS:
        assert font.lower() in output
    for tool in PDF_EVIDENCE_TOOLS:
        assert tool in output


def test_doctor_recommended_chinese_fonts_are_non_blocking(
    runner,
    cli_app,
    fake_toolchain_factory,
):
    fake_toolchain = fake_toolchain_factory()

    result = runner.invoke(
        cli_app,
        ["doctor"],
        env=fake_toolchain.env(missing_fonts=("MiSans", "Sarasa Gothic SC")),
    )

    assert result.exit_code == 0, result.output
    output = _normalized(result.output)
    assert "recommended chinese fonts" in output
    assert "misans" in output
    assert "sarasa gothic sc" in output
    assert "missing" in output


def test_doctor_fails_and_names_missing_executable(
    runner,
    cli_app,
    fake_toolchain_factory,
):
    fake_toolchain = fake_toolchain_factory(missing_executables={"latexmk"})

    result = runner.invoke(cli_app, ["doctor"], env=fake_toolchain.env())

    assert result.exit_code != 0, result.output
    assert "latexmk" in _normalized(result.output)
    _assert_actionable_failure(result.output)


@pytest.mark.parametrize("missing_tool", PDF_EVIDENCE_TOOLS)
def test_doctor_fails_and_names_missing_pdf_evidence_tool(
    runner,
    cli_app,
    fake_toolchain_factory,
    missing_tool,
):
    fake_toolchain = fake_toolchain_factory(missing_executables={missing_tool})

    result = runner.invoke(cli_app, ["doctor"], env=fake_toolchain.env())

    assert result.exit_code != 0, result.output
    output = _normalized(result.output)
    assert missing_tool in output
    assert "poppler" in output or "pdf evidence" in output
    _assert_actionable_failure(result.output)


@pytest.mark.parametrize("missing_font", REQUIRED_CJK_FONTS)
def test_doctor_fails_and_names_missing_noto_cjk_font(
    runner,
    cli_app,
    fake_toolchain_factory,
    missing_font,
):
    fake_toolchain = fake_toolchain_factory()

    result = runner.invoke(
        cli_app,
        ["doctor"],
        env=fake_toolchain.env(missing_fonts=(missing_font,)),
    )

    assert result.exit_code != 0, result.output
    output = _normalized(result.output)
    assert missing_font.lower() in output
    assert "font" in output
    _assert_actionable_failure(result.output)


def test_doctor_fails_and_names_missing_tex_package(
    runner,
    cli_app,
    fake_toolchain_factory,
):
    fake_toolchain = fake_toolchain_factory()

    result = runner.invoke(
        cli_app,
        ["doctor"],
        env=fake_toolchain.env(missing_tex_packages=("fontawesome5",)),
    )

    assert result.exit_code != 0, result.output
    assert "fontawesome5" in _normalized(result.output)
    _assert_actionable_failure(result.output)


def test_doctor_fixture_and_snapshot_layout_exists():
    test_root = Path(__file__).parent

    assert (test_root / "fixtures" / "doctor" / "required_toolchain.json").is_file()
    assert (test_root / "snapshots" / "doctor" / "doctor-ok-fragments.txt").is_file()
