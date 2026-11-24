"""Extract supported document formats into text and splitter heading hints."""

from __future__ import annotations

import io
import statistics
from dataclasses import dataclass
from pathlib import Path

from app.core.errors import ValidationError

MAX_SOURCE_BYTES = 200_000
MAX_EXTRACTED_CHARS = 200_000


@dataclass(frozen=True)
class ExtractedDocument:
    text: str
    heading_hints: dict[int, int]


def _unsupported() -> ValidationError:
    return ValidationError(
        "Supported file formats are .txt, .md, .docx and .pdf", "file_type_unsupported"
    )


def extract_document(filename: str | None, content: bytes) -> ExtractedDocument:
    if len(content) > MAX_SOURCE_BYTES:
        raise ValidationError("The uploaded file is too large", "file_too_large")
    suffix = Path(filename or "").suffix.lower()
    if suffix in {".txt", ".md"}:
        try:
            text = content.decode("utf-8")
            if len(text) > MAX_EXTRACTED_CHARS:
                raise ValidationError("The extracted document text is too large", "file_too_large")
            return ExtractedDocument(text, {})
        except UnicodeDecodeError as exc:
            raise ValidationError("The text file must use UTF-8 encoding", "file_invalid") from exc
    if suffix == ".docx":
        document = _extract_docx(content)
    elif suffix == ".pdf":
        document = _extract_pdf(content)
    else:
        raise _unsupported()
    if len(document.text) > MAX_EXTRACTED_CHARS:
        raise ValidationError("The extracted document text is too large", "file_too_large")
    return document


def _extract_docx(content: bytes) -> ExtractedDocument:
    try:
        from docx import Document

        document = Document(io.BytesIO(content))
        lines: list[str] = []
        hints: dict[int, int] = {}

        def add_line(value: str, level: int | None = None) -> None:
            value = value.strip()
            if not value:
                return
            offset = sum(len(line) + 1 for line in lines)
            lines.append(value)
            if level is not None:
                hints[offset] = max(1, min(level, 6))

        paragraphs = {id(paragraph._element): paragraph for paragraph in document.paragraphs}
        tables = {id(table._element): table for table in document.tables}
        for child in document.element.body.iterchildren():
            if id(child) in paragraphs:
                paragraph = paragraphs[id(child)]
                style = paragraph.style.name if paragraph.style else ""
                level = None
                if style.lower().startswith("heading"):
                    try:
                        level = int(style.split()[-1])
                    except ValueError:
                        level = 1
                add_line(paragraph.text, level)
            elif id(child) in tables:
                table = tables[id(child)]
                if not table.rows:
                    continue
                headers = [cell.text.strip() for cell in table.rows[0].cells]
                for row_index, row in enumerate(table.rows):
                    values = [cell.text.strip() for cell in row.cells]
                    if row_index == 0 and len(table.rows) > 1:
                        continue
                    if headers and len(headers) == len(values):
                        add_line(
                            " | ".join(
                                f"{header}: {value}"
                                for header, value in zip(headers, values, strict=False)
                            )
                        )
                    else:
                        add_line(" | ".join(values))
        return ExtractedDocument("\n".join(lines), hints)
    except Exception as exc:
        raise ValidationError("The DOCX file is damaged or unreadable", "file_invalid") from exc


def _extract_pdf(content: bytes) -> ExtractedDocument:
    try:
        import pdfplumber

        lines: list[str] = []
        hints: dict[int, int] = {}
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                page_lines = page_text.splitlines()
                words = page.extract_words(extra_attrs=["size", "fontname"])
                sizes = [float(word["size"]) for word in words if word.get("size")]
                threshold = statistics.median(sizes) * 1.2 if sizes else None
                groups: dict[float, list[dict[str, object]]] = {}
                for word in words:
                    groups.setdefault(round(float(word["top"]), 1), []).append(word)
                ordered_groups = [groups[key] for key in sorted(groups)]
                for index, line in enumerate(page_lines):
                    offset = sum(len(value) + 1 for value in lines)
                    lines.append(line)
                    line_words = ordered_groups[index] if index < len(ordered_groups) else []
                    bold = any(
                        "bold" in str(word.get("fontname", "")).lower() for word in line_words
                    )
                    large = (
                        threshold is not None
                        and line_words
                        and float(line_words[0].get("size", 0)) >= threshold
                    )
                    if line_words and (large or bold) and len(line) <= 120:
                        hints[offset] = 1
                if page_lines:
                    lines.append("")
        while lines and not lines[-1]:
            lines.pop()
        return ExtractedDocument("\n".join(lines), hints)
    except Exception as exc:
        raise ValidationError("The PDF file is damaged or unreadable", "file_invalid") from exc
