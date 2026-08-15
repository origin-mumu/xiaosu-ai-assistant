from pathlib import Path

import pymupdf
from docx import Document


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "documents"


def generate_docx() -> None:
    document = Document()
    document.add_heading("差旅与报销制度", level=1)
    sections = {
        "出差申请": "出差人员应至少提前 3 个工作日提交申请，写明目的地、事由、日期和预算。未经审批产生的费用原则上不予报销。",
        "交通标准": "国内出差优先选择高铁二等座或经济舱。确因时间紧急升级交通标准时，必须附部门负责人书面说明。",
        "住宿标准": "一线城市住宿上限为每晚 600 元，其他城市为每晚 450 元。两人同行且条件允许时优先安排双人间。",
        "报销材料": "报销需要差旅审批单、交通和住宿发票、行程单、支付凭证。出差结束后 10 个工作日内提交，超标费用须附说明。",
        "差旅补贴": "出差期间按自然日发放餐饮补贴，每人每天 100 元。由客户承担餐饮的日期不重复领取补贴。",
    }
    for title, body in sections.items():
        document.add_heading(title, level=2)
        document.add_paragraph(body)
    document.save(OUTPUT / "差旅与报销制度.docx")


def generate_pdf() -> None:
    document = pymupdf.open()
    pages = [
        (
            "Office Equipment Guide",
            "Standard package: laptop, charger and mouse. Development staff may request one external monitor. "
            "All equipment carries an asset number and must be confirmed when received.",
        ),
        (
            "Repair and Return",
            "Submit an IT service ticket before repair. Do not open the device or reinstall the operating system "
            "when data loss or a security incident is suspected. Return all assets on the final working day.",
        ),
    ]
    for title, body in pages:
        page = document.new_page()
        page.insert_text((72, 90), title, fontsize=20)
        page.insert_textbox((72, 130, 520, 720), body, fontsize=12, lineheight=1.5)
    document.save(OUTPUT / "office-equipment-guide.pdf")


if __name__ == "__main__":
    OUTPUT.mkdir(parents=True, exist_ok=True)
    generate_docx()
    generate_pdf()
    print(f"Generated sample documents in {OUTPUT}")
