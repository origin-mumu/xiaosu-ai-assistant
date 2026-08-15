from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import fitz
from docx import Document as WordDocument


class UnsupportedDocumentError(ValueError):
    pass


@dataclass(slots=True)
class TextSegment:
    text: str
    section_title: str | None = None
    page_number: int | None = None
    paragraph_number: int | None = None


SUPPORTED_EXTENSIONS = {".md", ".txt", ".pdf", ".docx"}


def parse_document(filename: str, content: bytes) -> list[TextSegment]:
    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise UnsupportedDocumentError(f"不支持 {extension or '无扩展名'}，仅支持 {supported}")
    if extension == ".pdf":
        return _parse_pdf(content)
    if extension == ".docx":
        return _parse_docx(content)
    text = _decode_text(content)
    return _parse_markdown(text) if extension == ".md" else _parse_plain_text(text)


def _decode_text(content: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("文本编码无法识别，请转换为 UTF-8 后重试")


def _parse_plain_text(text: str) -> list[TextSegment]:
    paragraphs = [part.strip() for part in text.replace("\r\n", "\n").split("\n\n")]
    return [
        TextSegment(text=paragraph, paragraph_number=index)
        for index, paragraph in enumerate((p for p in paragraphs if p), start=1)
    ]


def _parse_markdown(text: str) -> list[TextSegment]:
    segments: list[TextSegment] = []
    section: str | None = None
    buffer: list[str] = []
    paragraph = 0

    def flush() -> None:
        nonlocal paragraph
        body = "\n".join(buffer).strip()
        buffer.clear()
        if body:
            paragraph += 1
            segments.append(TextSegment(body, section_title=section, paragraph_number=paragraph))

    for line in text.replace("\r\n", "\n").splitlines():
        stripped = line.strip()
        if stripped.startswith("#") and stripped.lstrip("#").startswith(" "):
            flush()
            section = stripped.lstrip("#").strip()
        elif not stripped:
            flush()
        else:
            buffer.append(line)
    flush()
    return segments


def _parse_pdf(content: bytes) -> list[TextSegment]:
    segments: list[TextSegment] = []
    with fitz.open(stream=content, filetype="pdf") as document:
        for page_index, page in enumerate(document, start=1):
            blocks = page.get_text("blocks", sort=True)
            for paragraph, block in enumerate(blocks, start=1):
                text = str(block[4]).strip()
                if text:
                    segments.append(
                        TextSegment(
                            text=text,
                            page_number=page_index,
                            paragraph_number=paragraph,
                        )
                    )
    return segments


def _parse_docx(content: bytes) -> list[TextSegment]:
    document = WordDocument(BytesIO(content))
    segments: list[TextSegment] = []
    section: str | None = None
    paragraph_number = 0
    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if not text:
            continue
        style_name = paragraph.style.name.lower() if paragraph.style else ""
        if style_name.startswith("heading"):
            section = text
            continue
        paragraph_number += 1
        segments.append(
            TextSegment(
                text=text,
                section_title=section,
                paragraph_number=paragraph_number,
            )
        )
    return segments
