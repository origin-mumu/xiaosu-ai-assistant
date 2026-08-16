from __future__ import annotations

import io
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


def register_pdf_font() -> str:
    candidates = (
        Path("C:/Windows/Fonts/simhei.ttf"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    )
    for candidate in candidates:
        if candidate.exists():
            pdfmetrics.registerFont(TTFont("XiaosuCJK", str(candidate), subfontIndex=0))
            return "XiaosuCJK"
    raise RuntimeError("未找到可用于生成中文 PDF 的字体")


def draw_wrapped_text(
    pdf: canvas.Canvas,
    text: str,
    *,
    x: float,
    y: float,
    width: float,
    font: str,
    size: float,
    leading: float,
) -> float:
    line = ""
    lines: list[str] = []
    for character in text:
        candidate = line + character
        if pdfmetrics.stringWidth(candidate, font, size) <= width:
            line = candidate
        else:
            lines.append(line)
            line = character
    if line:
        lines.append(line)
    pdf.setFont(font, size)
    for content in lines:
        pdf.drawString(x, y, content)
        y -= leading
    return y


def generate_pdf(
    output: Path,
    filename: str,
    title: str,
    subtitle: str,
    sections: dict[str, str],
    banner: bytes,
) -> None:
    font = register_pdf_font()
    pdf = canvas.Canvas(str(output / filename), pagesize=letter, pageCompression=1)
    pdf.setTitle(title)
    pdf.setAuthor("小苏企业知识库")
    pdf.setSubject(subtitle)
    image = ImageReader(io.BytesIO(banner))

    pdf.drawImage(
        image, 42, 568, width=528, height=182, preserveAspectRatio=False, mask="auto"
    )
    pdf.setFillColor(HexColor("#F7F8FF"))
    pdf.setStrokeColor(HexColor("#E5E8F5"))
    pdf.roundRect(42, 142, 528, 382, 16, stroke=1, fill=1)
    pdf.setFillColor(HexColor("#19274B"))
    pdf.setFont(font, 25)
    pdf.drawString(72, 450, title)
    pdf.setFillColor(HexColor("#59698F"))
    pdf.setFont(font, 13)
    pdf.drawString(72, 405, subtitle)
    pdf.setFont(font, 10)
    pdf.drawString(72, 208, "小苏企业知识库｜内部参考资料｜2026 年 8 月")
    pdf.showPage()

    for page_number, (heading, body) in enumerate(sections.items(), start=2):
        pdf.setFillColor(HexColor("#4A5DE6"))
        pdf.roundRect(42, 680, 528, 70, 14, stroke=0, fill=1)
        pdf.setFillColor(HexColor("#FFFFFF"))
        pdf.setFont(font, 18)
        pdf.drawString(66, 706, heading)
        pdf.setFillColor(HexColor("#1F2B49"))
        draw_wrapped_text(
            pdf, body, x=66, y=620, width=480, font=font, size=12.5, leading=25
        )
        pdf.setStrokeColor(HexColor("#DCE0EC"))
        pdf.line(66, 96, 546, 96)
        pdf.setFillColor(HexColor("#7B879F"))
        pdf.setFont(font, 8.5)
        pdf.drawString(66, 74, "小苏企业知识库 · 可检索原文")
        pdf.drawRightString(546, 74, str(page_number))
        pdf.showPage()

    pdf.save()
