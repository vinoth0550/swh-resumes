# templates.py
# CLEAN COMBINED TEMPLATES (1,2,3)

from fastapi.responses import FileResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

import language_tool_python
import tempfile
import os
import re

# ---------------------------------------------------------
#  SHARED FONT REGISTRATION (Only Once)
# ---------------------------------------------------------

FONTS_DIR = r"C:\Windows\Fonts"

FONT_MAP = {
    "Arial": "arial.ttf",
    "Arial-Bold": "arialbd.ttf",
    "Calibri": "calibri.ttf",
    "Calibri-Bold": "calibrib.ttf",
    "Times-Roman": "times.ttf",
    "Times-Bold": "timesbd.ttf",
}

def register_all_fonts():
    for font_name, file_name in FONT_MAP.items():
        font_path = os.path.join(FONTS_DIR, file_name)
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont(font_name, font_path))
            except:
                pass

register_all_fonts()

# ---------------------------------------------------------
#  SHARED HELPER FUNCTIONS
# ---------------------------------------------------------

def wrap_text_dynamic(c, text, font_name, font_size, max_width):
    c.setFont(font_name, font_size)
    lines = []
    for paragraph in (text or "").split("\n"):
        if not paragraph.strip():
            lines.append("")
            continue

        words = paragraph.split(" ")
        line = ""
        for word in words:
            test_line = (line + " " + word).strip()
            if c.stringWidth(test_line, font_name, font_size) <= max_width:
                line = test_line
            else:
                if c.stringWidth(word, font_name, font_size) > max_width:
                    subword = ""
                    for ch in word:
                        if c.stringWidth(subword + ch, font_name, font_size) <= max_width:
                            subword += ch
                        else:
                            lines.append(subword)
                            subword = ch
                    line = subword
                else:
                    lines.append(line)
                    line = word
        if line:
            lines.append(line)
    return lines


# # ---------------------------------------------------------
# #  GRAMMAR AUTO-CORRECT
# # ---------------------------------------------------------

# tool = language_tool_python.LanguageTool('en-US')

# def auto_correct_text(text):
#     if not text:
#         return text
#     try:
#         matches = tool.check(text)
#         corrected = language_tool_python.utils.correct(text, matches)
#         corrected = re.sub(
#             r'([^\w\s]\s*)([a-z])',
#             lambda m: m.group(1) + m.group(2).upper(),
#             corrected
#         )
#         return corrected
#     except:
#         return text


# ---------------------------------------------------------
#  SHARED DRAW FUNCTION (used by all templates)
# ---------------------------------------------------------

def draw_resume(c, style, data):
    width, height = A4
    margin = 40
    sidebar_width = width * style["sidebar_width"]
    font_name = style["font_name"]
    font_name_bold = style["font_name_bold"]

    # Sidebar background
    c.setFillColor(style["sidebar_bg"])
    c.rect(0, 0, sidebar_width, height, fill=True, stroke=False)

    # TEXT SETTINGS
    title_size = style["font_sizes"]["title"]
    job_size   = style["font_sizes"].get("job_role", 14)
    header_size = style["font_sizes"]["header"]
    body_size = style["font_sizes"]["body"]

    # Draw Name
    y = height - margin
    c.setFont(font_name_bold, title_size)
    c.setFillColor(style["primary"])
    c.drawString(sidebar_width + margin, y, data["full_name"].upper())
    y -= title_size + 5

    # Draw Job Role
    if data.get("job_role"):
        c.setFont(font_name_bold, job_size)
        c.setFillColor(style["primary"])
        c.drawString(sidebar_width + margin, y, data["job_role"])
        y -= job_size + 15

    # Sections
    sidebar_sections = [
        ("email", "Email"),
        ("phone", "Phone"),
        ("skills", data["skills_header"]),
        ("languages", data["languages_header"]),
        ("certifications", data["certifications_header"]),
    ]

    main_sections = [
        ("profile_summary", data["profile_summary_header"]),
        ("work_experience", data["work_experience_header"]),
        ("education", data["education_header"]),
        ("interests", data["interests_header"]),
    ]

    # Draw Sidebar Content
    sy = height - margin - 20
    sx = 15

    for key, header in sidebar_sections:
        if not data.get(key):
            continue
        c.setFont(font_name_bold, header_size)
        c.setFillColor(style["primary"])
        c.drawString(sx, sy, header.upper())
        sy -= header_size + 5

        lines = wrap_text_dynamic(c, data[key], font_name, body_size, sidebar_width - 20)
        c.setFont(font_name, body_size)
        c.setFillColor(colors.black)
        for line in lines:
            c.drawString(sx, sy, line)
            sy -= body_size + 2
        sy -= 10

    # Draw Main Sections
    for key, header in main_sections:
        if not data.get(key):
            continue

        c.setFont(font_name_bold, header_size)
        c.setFillColor(style["primary"])
        c.drawString(sidebar_width + margin, y, header.upper())
        y -= header_size + 5

        lines = wrap_text_dynamic(
            c, data[key], font_name, body_size,
            width - sidebar_width - margin * 2
        )
        c.setFont(font_name, body_size)
        for line in lines:
            c.drawString(sidebar_width + margin, y, line)
            y -= body_size + 2
        y -= 10


# ---------------------------------------------------------
#  STYLE DEFINITIONS (3 Templates)
# ---------------------------------------------------------

TEMPLATE_STYLES = {
    "classic": {
        "primary": colors.black,
        "sidebar_bg": colors.white,
        "sidebar_width": 0.28,
        "font_name": "Times-Roman",
        "font_name_bold": "Times-Bold",
        "font_sizes": {"title": 18, "job_role": 16, "header": 12, "body": 11},
    },

    "modern_green": {
        "primary": colors.HexColor("#27AE60"),
        "sidebar_bg": colors.HexColor("#ECF0F1"),
        "sidebar_width": 0.30,
        "font_name": "Calibri",
        "font_name_bold": "Calibri-Bold",
        "font_sizes": {"title": 22, "job_role": 16, "header": 12, "body": 11},
    },

    "creative_teal": {
        "primary": colors.HexColor("#12A89D"),
        "sidebar_bg": colors.HexColor("#F8F9FA"),
        "sidebar_width": 0.32,
        "font_name": "Arial",
        "font_name_bold": "Arial-Bold",
        "font_sizes": {"title": 18, "job_role": 16, "header": 12, "body": 11},
    }
}

# ---------------------------------------------------------
#  TEMPLATE GENERATORS (USED BY main.py)
# ---------------------------------------------------------

def template1(data):
    """Classic Black Template"""
    # data = {k: auto_correct_text(str(v)) for k, v in data.__dict__.items()}
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    c = canvas.Canvas(tmp.name, pagesize=A4)
    draw_resume(c, TEMPLATE_STYLES["classic"], data)
    c.save()
    return FileResponse(tmp.name, media_type="application/pdf")


def template2(data):
    """Modern Green Template"""
    # data = {k: auto_correct_text(str(v)) for k, v in data.__dict__.items()}
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    c = canvas.Canvas(tmp.name, pagesize=A4)
    draw_resume(c, TEMPLATE_STYLES["modern_green"], data)
    c.save()
    return FileResponse(tmp.name, media_type="application/pdf")


def template3(data):
    """Creative Teal Template"""
    # data = {k: auto_correct_text(str(v)) for k, v in data.__dict__.items()}
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    c = canvas.Canvas(tmp.name, pagesize=A4)
    draw_resume(c, TEMPLATE_STYLES["creative_teal"], data)
    c.save()
    return FileResponse(tmp.name, media_type="application/pdf")


# EXPORT LIST FOR main.py
templates = [template1, template2, template3]
