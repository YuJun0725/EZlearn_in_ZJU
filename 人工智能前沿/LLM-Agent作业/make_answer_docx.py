from __future__ import annotations

import re
import sys
from html import escape
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


SOURCE = Path("LLM_Agent作业解答.md")
OUTPUT = Path("LLM_Agent作业解答.docx")

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def clean_inline(text: str) -> str:
    return text.replace("`", "")


def run(text: str, bold: bool = False, size: int | None = None, mono: bool = False) -> str:
    rpr = []
    if bold:
        rpr.append("<w:b/>")
    if size:
        rpr.append(f'<w:sz w:val="{size}"/>')
        rpr.append(f'<w:szCs w:val="{size}"/>')
    if mono:
        rpr.append('<w:rFonts w:ascii="Consolas" w:hAnsi="Consolas" w:eastAsia="Microsoft YaHei"/>')
    else:
        rpr.append('<w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="Microsoft YaHei"/>')
    rpr_xml = "<w:rPr>" + "".join(rpr) + "</w:rPr>"
    space = ' xml:space="preserve"' if text[:1].isspace() or text[-1:].isspace() else ""
    return f"<w:r>{rpr_xml}<w:t{space}>{escape(text)}</w:t></w:r>"


def para(text: str = "", style: str | None = None, indent: bool = False, mono: bool = False) -> str:
    ppr_parts = []
    if style:
        ppr_parts.append(f'<w:pStyle w:val="{style}"/>')
    if indent:
        ppr_parts.append('<w:ind w:left="420"/>')
    ppr = "<w:pPr>" + "".join(ppr_parts) + "</w:pPr>" if ppr_parts else ""
    size = 20 if mono else None
    return f"<w:p>{ppr}{run(clean_inline(text), mono=mono, size=size)}</w:p>"


def cell(text: str) -> str:
    return (
        '<w:tc><w:tcPr><w:tcW w:w="2400" w:type="dxa"/>'
        '<w:tcMar><w:top w:w="80" w:type="dxa"/><w:left w:w="120" w:type="dxa"/>'
        '<w:bottom w:w="80" w:type="dxa"/><w:right w:w="120" w:type="dxa"/></w:tcMar></w:tcPr>'
        + para(clean_inline(text))
        + "</w:tc>"
    )


def table(rows: list[list[str]]) -> str:
    border = (
        '<w:top w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
        '<w:left w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
        '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
        '<w:right w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
        '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
        '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
    )
    parts = [
        '<w:tbl><w:tblPr><w:tblW w:w="0" w:type="auto"/><w:tblBorders>'
        + border
        + "</w:tblBorders></w:tblPr>"
    ]
    for row in rows:
        parts.append("<w:tr>" + "".join(cell(item.strip()) for item in row) + "</w:tr>")
    parts.append("</w:tbl>")
    return "".join(parts)


def split_table_line(line: str) -> list[str]:
    return [part.strip() for part in line.strip().strip("|").split("|")]


def is_separator(row: list[str]) -> bool:
    return all(re.fullmatch(r":?-{3,}:?", item.strip()) for item in row)


def markdown_to_body(markdown: str) -> str:
    body = []
    lines = markdown.splitlines()
    i = 0
    in_code = False
    code_lines: list[str] = []

    while i < len(lines):
        line = lines[i]

        if line.startswith("```"):
            if not in_code:
                in_code = True
                code_lines = []
            else:
                in_code = False
                for code in code_lines:
                    body.append(para(code, mono=True))
            i += 1
            continue

        if in_code:
            code_lines.append(line)
            i += 1
            continue

        if not line.strip():
            body.append(para())
            i += 1
            continue

        if line.strip().startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                row = split_table_line(lines[i])
                if not is_separator(row):
                    rows.append(row)
                i += 1
            if rows:
                body.append(table(rows))
            continue

        if line.startswith("# "):
            body.append(para(line[2:].strip(), style="Title"))
        elif line.startswith("## "):
            body.append(para(line[3:].strip(), style="Heading1"))
        elif line.startswith("### "):
            body.append(para(line[4:].strip(), style="Heading2"))
        elif re.match(r"^\d+\.\s+", line):
            body.append(para(line.strip(), indent=True))
        else:
            body.append(para(line.strip()))
        i += 1

    return "".join(body)


def build_docx() -> None:
    markdown = SOURCE.read_text(encoding="utf-8")
    body_xml = markdown_to_body(markdown)

    document_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{W_NS}" xmlns:r="{R_NS}"><w:body>{body_xml}<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" w:footer="720" w:gutter="0"/></w:sectPr></w:body></w:document>'''

    styles_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="{W_NS}">
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="Microsoft YaHei"/><w:sz w:val="22"/><w:szCs w:val="22"/></w:rPr><w:pPr><w:spacing w:after="120" w:line="300" w:lineRule="auto"/></w:pPr></w:style>
<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:rPr><w:b/><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="Microsoft YaHei"/><w:sz w:val="36"/><w:szCs w:val="36"/></w:rPr><w:pPr><w:spacing w:after="300"/></w:pPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:rPr><w:b/><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="Microsoft YaHei"/><w:sz w:val="30"/><w:szCs w:val="30"/></w:rPr><w:pPr><w:spacing w:before="240" w:after="160"/><w:outlineLvl w:val="0"/></w:pPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:rPr><w:b/><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="Microsoft YaHei"/><w:sz w:val="26"/><w:szCs w:val="26"/></w:rPr><w:pPr><w:spacing w:before="200" w:after="120"/><w:outlineLvl w:val="1"/></w:pPr></w:style>
</w:styles>'''

    content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/></Types>'''

    rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>'''

    doc_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>'''

    with ZipFile(OUTPUT, "w", ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("word/document.xml", document_xml)
        zf.writestr("word/styles.xml", styles_xml)
        zf.writestr("word/_rels/document.xml.rels", doc_rels)


if __name__ == "__main__":
    build_docx()
    print(OUTPUT)
