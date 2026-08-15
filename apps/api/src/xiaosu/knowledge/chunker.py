from dataclasses import dataclass

from xiaosu.knowledge.parser import TextSegment


@dataclass(slots=True)
class TextChunk:
    content: str
    section_title: str | None
    page_number: int | None
    paragraph_start: int | None
    paragraph_end: int | None


def chunk_segments(
    segments: list[TextSegment],
    chunk_size: int = 700,
    overlap: int = 100,
) -> list[TextChunk]:
    chunks: list[TextChunk] = []
    for segment in segments:
        text = " ".join(segment.text.split())
        if not text:
            continue
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            if end < len(text):
                boundary = text.rfind("。", start, end)
                if boundary > start + chunk_size // 2:
                    end = boundary + 1
            chunks.append(
                TextChunk(
                    content=text[start:end],
                    section_title=segment.section_title,
                    page_number=segment.page_number,
                    paragraph_start=segment.paragraph_number,
                    paragraph_end=segment.paragraph_number,
                )
            )
            if end >= len(text):
                break
            start = max(end - overlap, start + 1)
    return chunks
