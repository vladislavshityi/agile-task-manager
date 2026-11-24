import io

import pytest

from app.core.errors import ValidationError
from app.modules.analysis.documents import MAX_SOURCE_BYTES, extract_document


def test_text_and_markdown_keep_offsets() -> None:
    source = "# Заголовок\n\nТекст."
    extracted = extract_document("spec.md", source.encode())
    assert extracted.text == source
    assert extracted.heading_hints == {}


def test_unsupported_invalid_and_too_large_files() -> None:
    with pytest.raises(ValidationError) as unsupported:
        extract_document("spec.rtf", b"text")
    assert unsupported.value.code == "file_type_unsupported"

    with pytest.raises(ValidationError) as invalid:
        extract_document("spec.txt", b"\xff")
    assert invalid.value.code == "file_invalid"

    with pytest.raises(ValidationError) as too_large:
        extract_document("spec.txt", b"x" * (MAX_SOURCE_BYTES + 1))
    assert too_large.value.code == "file_too_large"


def test_docx_preserves_block_order_and_table_headers() -> None:
    docx = pytest.importorskip("docx")
    document = docx.Document()
    document.add_paragraph("До таблицы")
    heading = document.add_paragraph("Раздел")
    heading.style = "Heading 1"
    table = document.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "Имя"
    table.cell(0, 1).text = "Статус"
    table.cell(1, 0).text = "Задача"
    table.cell(1, 1).text = "Готово"
    document.add_paragraph("После таблицы")
    buffer = io.BytesIO()
    document.save(buffer)

    extracted = extract_document("spec.docx", buffer.getvalue())
    assert extracted.text.splitlines() == [
        "До таблицы",
        "Раздел",
        "Имя: Задача | Статус: Готово",
        "После таблицы",
    ]
    assert extracted.heading_hints[extracted.text.index("Раздел")] == 1


def test_docx_extracted_text_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    docx = pytest.importorskip("docx")
    import app.modules.analysis.documents as documents

    document = docx.Document()
    document.add_paragraph("long text")
    buffer = io.BytesIO()
    document.save(buffer)
    monkeypatch.setattr(documents, "MAX_EXTRACTED_CHARS", 3)
    with pytest.raises(ValidationError) as error:
        documents.extract_document("spec.docx", buffer.getvalue())
    assert error.value.code == "file_too_large"
