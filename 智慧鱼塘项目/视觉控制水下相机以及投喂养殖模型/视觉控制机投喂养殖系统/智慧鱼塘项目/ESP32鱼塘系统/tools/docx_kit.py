# -*- coding: utf-8 -*-
"""
docx_kit —— 生成中文技术文档的 python-docx 封装
提供：封面、目录域、多级标题、正文、要点、表格、提示框、引文、页脚页码
"""
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# ---------- 配色 ----------
C_INK = RGBColor(0x1A, 0x1A, 0x1A)
C_MUTED = RGBColor(0x5A, 0x6B, 0x66)
C_ACCENT = RGBColor(0x0B, 0x6E, 0x4F)      # 深水绿
C_WARN = RGBColor(0xA8, 0x5A, 0x00)
C_ALARM = RGBColor(0xB3, 0x2C, 0x1A)
C_CYAN = RGBColor(0x0E, 0x63, 0x74)
C_VIOLET = RGBColor(0x5B, 0x3A, 0x8C)

BG_HEAD = "0B6E4F"
BG_ALT = "F2F7F5"
BG_WARN = "FFF6E5"
BG_ALARM = "FDECEA"
BG_INFO = "EAF4F1"
BG_CODE = "F4F6F5"

FONT_H = "微软雅黑"
FONT_B = "宋体"
FONT_M = "Consolas"


# ---------------- 底层工具 ----------------
def _set_run_font(run, name=None, size=None, bold=None, color=None, mono=False, italic=None):
    f = run.font
    if size is not None:
        f.size = Pt(size)
    if bold is not None:
        f.bold = bold
    if italic is not None:
        f.italic = italic
    if color is not None:
        f.color.rgb = color
    nm = FONT_M if mono else (name or FONT_B)
    f.name = nm
    rPr = run._element.get_or_add_rPr()
    rf = rPr.find(qn('w:rFonts'))
    if rf is None:
        rf = OxmlElement('w:rFonts')
        rPr.append(rf)
    rf.set(qn('w:ascii'), nm)
    rf.set(qn('w:hAnsi'), nm)
    rf.set(qn('w:eastAsia'), FONT_H if not mono else nm)


def _props(obj):
    """接受 _Cell / _Paragraph / 原始 lxml 元素，返回 (属性容器, 是否表格单元格)"""
    if hasattr(obj, '_tc'):                       # docx _Cell
        return obj._tc.get_or_add_tcPr(), True
    if hasattr(obj, '_p'):                        # docx _Paragraph
        return obj._p.get_or_add_pPr(), False
    if hasattr(obj, 'tag') and obj.tag.endswith('}tc'):
        return obj.get_or_add_tcPr(), True
    return obj.get_or_add_pPr(), False


def _shade(el, fill):
    pr, _ = _props(el)
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill)
    pr.append(shd)


def _borders(el, color="D8E3DF", sz=6, sides=("top", "left", "bottom", "right")):
    pr, is_cell = _props(el)
    bd = OxmlElement('w:tcBorders' if is_cell else 'w:pBdr')
    for s in sides:
        e = OxmlElement('w:' + s)
        e.set(qn('w:val'), 'single')
        e.set(qn('w:sz'), str(sz))
        e.set(qn('w:space'), '0')
        e.set(qn('w:color'), color)
        bd.append(e)
    pr.append(bd)


def _spacing(p, before=0, after=6, line=1.5):
    pf = p.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.line_spacing = line


def _field(paragraph, instr):
    r = paragraph.add_run()
    fc = OxmlElement('w:fldChar'); fc.set(qn('w:fldCharType'), 'begin')
    it = OxmlElement('w:instrText'); it.set(qn('xml:space'), 'preserve'); it.text = instr
    fc2 = OxmlElement('w:fldChar'); fc2.set(qn('w:fldCharType'), 'separate')
    t = OxmlElement('w:t'); t.text = "按 F9 更新"
    fc3 = OxmlElement('w:fldChar'); fc3.set(qn('w:fldCharType'), 'end')
    r._r.append(fc); r._r.append(it); r._r.append(fc2); r._r.append(t); r._r.append(fc3)
    return r


# ---------------- 文档骨架 ----------------
def new_doc(margin_cm=2.4):
    doc = Document()
    for s in doc.sections:
        s.top_margin = Cm(margin_cm)
        s.bottom_margin = Cm(margin_cm)
        s.left_margin = Cm(margin_cm + 0.4)
        s.right_margin = Cm(margin_cm + 0.4)
    st = doc.styles['Normal']
    st.font.size = Pt(10.5)
    st.font.name = FONT_B
    st.element.rPr.rFonts.set(qn('w:eastAsia'), FONT_B)
    st.paragraph_format.line_spacing = 1.5
    st.paragraph_format.space_after = Pt(6)
    return doc


def cover(doc, kicker, title, subtitle, meta_rows, footer_note=None):
    for _ in range(3):
        doc.add_paragraph()
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _spacing(p, 0, 10)
    _set_run_font(p.add_run(kicker), FONT_H, 11, True, C_ACCENT)

    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _spacing(p, 0, 6, 1.25)
    _set_run_font(p.add_run(title), FONT_H, 26, True, C_INK)

    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _spacing(p, 0, 26)
    _set_run_font(p.add_run(subtitle), FONT_H, 12, False, C_MUTED)

    t = doc.add_table(rows=0, cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for k, v in meta_rows:
        row = t.add_row().cells
        row[0].width = Cm(4.6); row[1].width = Cm(9.4)
        pa = row[0].paragraphs[0]; _spacing(pa, 3, 3, 1.2)
        _set_run_font(pa.add_run(k), FONT_H, 10, True, C_MUTED)
        pb = row[1].paragraphs[0]; _spacing(pb, 3, 3, 1.2)
        _set_run_font(pb.add_run(v), FONT_B, 10, False, C_INK)
        for c in row:
            _borders(c, "E4EBE8", 4, ("bottom",))

    if footer_note:
        doc.add_paragraph()
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _spacing(p, 10, 0)
        _set_run_font(p.add_run(footer_note), FONT_B, 9, False, C_MUTED)
    doc.add_page_break()


def toc(doc, title="目 录"):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _spacing(p, 0, 16)
    _set_run_font(p.add_run(title), FONT_H, 18, True, C_INK)
    p = doc.add_paragraph()
    _spacing(p, 0, 0, 1.4)
    _field(p, r' TOC \o "1-3" \h \z \u ')
    p2 = doc.add_paragraph(); p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _spacing(p2, 4, 0)
    _set_run_font(p2.add_run("（在 Word 中按 Ctrl+A 再按 F9 可刷新页码）"), FONT_B, 9, False, C_MUTED)
    doc.add_page_break()


def footer_pagenum(doc, left_text):
    sec = doc.sections[0]
    f = sec.footer
    p = f.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_run_font(p.add_run(left_text + "    ·    第 "), FONT_B, 8.5, False, C_MUTED)
    r = _field(p, " PAGE ")
    _set_run_font(r, FONT_B, 8.5, False, C_MUTED)
    _set_run_font(p.add_run(" 页 / 共 "), FONT_B, 8.5, False, C_MUTED)
    r2 = _field(p, " NUMPAGES ")
    _set_run_font(r2, FONT_B, 8.5, False, C_MUTED)
    _set_run_font(p.add_run(" 页"), FONT_B, 8.5, False, C_MUTED)


# ---------------- 内容元素 ----------------
def h1(doc, text):
    doc.add_page_break()
    p = doc.add_paragraph()
    _spacing(p, 0, 12, 1.3)
    _set_run_font(p.add_run(text), FONT_H, 19, True, C_ACCENT)
    _borders(p, "0B6E4F", 12, ("bottom",))
    return p


def h1_nobreak(doc, text):
    p = doc.add_paragraph()
    _spacing(p, 14, 10, 1.3)
    _set_run_font(p.add_run(text), FONT_H, 19, True, C_ACCENT)
    _borders(p, "0B6E4F", 12, ("bottom",))
    return p


def h2(doc, text):
    p = doc.add_paragraph()
    _spacing(p, 14, 7, 1.3)
    _set_run_font(p.add_run(text), FONT_H, 14, True, C_INK)
    return p


def h3(doc, text):
    p = doc.add_paragraph()
    _spacing(p, 10, 5, 1.3)
    _set_run_font(p.add_run(text), FONT_H, 11.5, True, C_CYAN)
    return p


def para(doc, text, indent=True, size=10.5, after=6):
    p = doc.add_paragraph()
    _spacing(p, 0, after, 1.5)
    if indent:
        p.paragraph_format.first_line_indent = Pt(21)
    _set_run_font(p.add_run(text), FONT_B, size, False, C_INK)
    return p


def rich(doc, parts, indent=False, after=6, size=10.5):
    """parts: [(text, {bold/color/mono/size}), ...]"""
    p = doc.add_paragraph()
    _spacing(p, 0, after, 1.5)
    if indent:
        p.paragraph_format.first_line_indent = Pt(21)
    for text, opt in parts:
        _set_run_font(p.add_run(text), opt.get('font', FONT_B), opt.get('size', size),
                      opt.get('bold'), opt.get('color'), opt.get('mono', False))
    return p


def bullet(doc, text, level=0, color=None, size=10.5):
    p = doc.add_paragraph(style='List Bullet' if level == 0 else 'List Bullet 2')
    _spacing(p, 0, 3, 1.4)
    p.paragraph_format.left_indent = Cm(0.75 + level * 0.6)
    _set_run_font(p.add_run(text), FONT_B, size, False, color or C_INK)
    return p


def numbered(doc, text, size=10.5):
    p = doc.add_paragraph(style='List Number')
    _spacing(p, 0, 3, 1.4)
    p.paragraph_format.left_indent = Cm(0.75)
    _set_run_font(p.add_run(text), FONT_B, size, False, C_INK)
    return p


def kv_box(doc, title, body, kind="info"):
    """带左侧色条与浅底的提示框"""
    bg = {"info": BG_INFO, "warn": BG_WARN, "alarm": BG_ALARM, "code": BG_CODE}[kind]
    col = {"info": "0B6E4F", "warn": "C77700", "alarm": "C0392B", "code": "4A5A55"}[kind]
    t = doc.add_table(rows=1, cols=1)
    c = t.rows[0].cells[0]
    _shade(c._tc, bg)
    _borders(c, col, 4, ("top", "bottom", "right"))
    _borders(c, col, 18, ("left",))
    p = c.paragraphs[0]; _spacing(p, 4, 2, 1.35)
    tc = {"info": C_ACCENT, "warn": C_WARN, "alarm": C_ALARM, "code": C_MUTED}[kind]
    _set_run_font(p.add_run(title), FONT_H, 10.5, True, tc)
    for i, ln in enumerate(body if isinstance(body, list) else [body]):
        pp = c.add_paragraph() if i or True else p
        _spacing(pp, 0, 3, 1.4)
        _set_run_font(pp.add_run(ln), FONT_B, 9.5, False, C_INK)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def quote(doc, text, source=None):
    t = doc.add_table(rows=1, cols=1)
    c = t.rows[0].cells[0]
    _borders(c, "0B6E4F", 18, ("left",))
    _borders(c, "FFFFFF", 2, ("top", "bottom", "right"))
    p = c.paragraphs[0]; _spacing(p, 4, 2, 1.5)
    _set_run_font(p.add_run(text), FONT_H, 10.5, False, RGBColor(0x2A, 0x3A, 0x35))
    if source:
        pp = c.add_paragraph(); _spacing(pp, 2, 4, 1.3)
        _set_run_font(pp.add_run("—— " + source), FONT_B, 9, False, C_MUTED)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def table(doc, headers, rows, widths=None, caption=None, note=None, align_num=True):
    if caption:
        p = doc.add_paragraph(); _spacing(p, 8, 4)
        _set_run_font(p.add_run(caption), FONT_H, 10, True, C_INK)
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = 'Table Grid'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = t.rows[0].cells
    for i, htxt in enumerate(headers):
        _shade(hdr[i]._tc, BG_HEAD)
        p = hdr[i].paragraphs[0]; _spacing(p, 2, 2, 1.25)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _set_run_font(p.add_run(htxt), FONT_H, 9, True, RGBColor(0xFF, 0xFF, 0xFF))
    for ri, row in enumerate(rows):
        cells = t.add_row().cells
        for i, val in enumerate(row):
            if ri % 2 == 1:
                _shade(cells[i]._tc, BG_ALT)
            p = cells[i].paragraphs[0]; _spacing(p, 2, 2, 1.3)
            txt = str(val)
            mono = align_num and i > 0 and txt[:1].isdigit()
            if mono:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            _set_run_font(p.add_run(txt), FONT_M if mono else FONT_B, 9 if mono else 9.5,
                          False, C_INK if not mono else RGBColor(0x0B, 0x4A, 0x38),
                          mono=mono)
    if widths:
        for r in t.rows:
            for i, w in enumerate(widths):
                r.cells[i].width = Cm(w)
    if note:
        p = doc.add_paragraph(); _spacing(p, 3, 8, 1.35)
        _set_run_font(p.add_run(note), FONT_B, 8.5, False, C_MUTED)
    else:
        doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def spacer(doc, pt=8):
    p = doc.add_paragraph(); _spacing(p, 0, pt)
    return p
