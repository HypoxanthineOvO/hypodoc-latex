from __future__ import annotations

import base64
import importlib
from collections.abc import Mapping

import pytest


SAMPLE_PDF_B64 = (
    "JVBERi0xLjQKJeLjz9MKMSAwIG9iago8PCAvVHlwZSAvQ2F0YWxvZyAvUGFnZXMg"
    "MiAwIFIgPj4KZW5kb2JqCjIgMCBvYmoKPDwgL1R5cGUgL1BhZ2VzIC9LaWRzIFsz"
    "IDAgUl0gL0NvdW50IDEgPj4KZW5kb2JqCjMgMCBvYmoKPDwgL1R5cGUgL1BhZ2Ug"
    "L1BhcmVudCAyIDAgUiAvTWVkaWFCb3ggWzAgMCA1OTUgODQyXSAvUmVzb3VyY2Vz"
    "IDw8IC9Gb250IDw8IC9GMSA0IDAgUiA+PiA+PiAvQ29udGVudHMgNSAwIFIgPj4K"
    "ZW5kb2JqCjQgMCBvYmoKPDwgL1R5cGUgL0ZvbnQgL1N1YnR5cGUgL1R5cGUxIC9C"
    "YXNlRm9udCAvSGVsdmV0aWNhID4+CmVuZG9iago1IDAgb2JqCjw8IC9MZW5ndGgg"
    "ODMgPj4Kc3RyZWFtCkJUCi9GMSAyNCBUZgo3MiA3NjAgVGQKKEh5cG8gUERGIEV2"
    "aWRlbmNlIFNhbXBsZSkgVGoKMCAtMzIgVGQKKEVuZ2xpc2ggdGV4dCkgVGoKRVQK"
    "ZW5kc3RyZWFtCmVuZG9iagp4cmVmCjAgNgowMDAwMDAwMDAwIDY1NTM1IGYgCjAw"
    "MDAwMDAwMTUgMDAwMDAgbiAKMDAwMDAwMDA2NCAwMDAwMCBuIAowMDAwMDAwMTIx"
    "IDAwMDAwIG4gCjAwMDAwMDAyNDcgMDAwMDAgbiAKMDAwMDAwMDMxNyAwMDAwMCBu"
    "IAp0cmFpbGVyCjw8IC9TaXplIDYgL1Jvb3QgMSAwIFIgPj4Kc3RhcnR4cmVmCjQ0"
    "OQolJUVPRgo="
)


def _pdf_evidence_module():
    try:
        return importlib.import_module("hypolatex.pdf_evidence")
    except ModuleNotFoundError as exc:
        if exc.name != "hypolatex.pdf_evidence":
            raise
        pytest.fail(
            "Expected hypolatex.pdf_evidence with read_pdf_info(), "
            "extract_text(), and render_page_png() helpers.",
            pytrace=False,
        )


@pytest.fixture
def sample_pdf(tmp_path):
    pdf_path = tmp_path / "sample-a4.pdf"
    pdf_path.write_bytes(base64.b64decode(SAMPLE_PDF_B64))
    return pdf_path


def test_pdf_evidence_reads_pdfinfo_as_normalized_mapping(sample_pdf):
    pdf_evidence = _pdf_evidence_module()

    info = pdf_evidence.read_pdf_info(sample_pdf)

    assert isinstance(info, Mapping)
    assert info["pages"] == "1"
    assert info["pdf_version"] == "1.4"
    assert "595 x 842 pts" in info["page_size"]
    assert "A4" in info["page_size"]


def test_pdf_evidence_extracts_text_from_pdf(sample_pdf):
    pdf_evidence = _pdf_evidence_module()

    text = pdf_evidence.extract_text(sample_pdf)

    assert "Hypo PDF Evidence Sample" in text
    assert "English text" in text


def test_pdf_evidence_renders_non_empty_png_screenshot(sample_pdf, tmp_path):
    pdf_evidence = _pdf_evidence_module()
    screenshot_dir = tmp_path / "screenshots"

    screenshot_path = pdf_evidence.render_page_png(
        sample_pdf,
        output_dir=screenshot_dir,
        page=1,
        stem="sample-page",
    )

    assert screenshot_path.suffix == ".png"
    assert screenshot_path.is_file()
    assert screenshot_path.stat().st_size > 0
    assert screenshot_path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
