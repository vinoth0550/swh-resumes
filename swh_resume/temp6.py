

# temp6.py

# this header changable template and data will be in body and raw json format

from fastapi import FastAPI, Form, HTTPException, File, UploadFile
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask # Import BackgroundTask
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os, tempfile, uuid, re, shutil
import language_tool_python
from reportlab.lib.utils import ImageReader
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel, Field
from typing import Optional



class ResumeData(BaseModel):
    full_name: str
    job_role: Optional[str] = ""
    email: str
    phone: str
    profile_summary: Optional[str] = ""
    work_experience: Optional[str] = ""
    education: Optional[str] = ""
    skills: Optional[str] = ""
    languages: Optional[str] = ""
    certifications: Optional[str] = ""

    # awards: Optional[str] = ""

    interests: Optional[str] = ""


app = FastAPI(title="Resume PDF Generator")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# FONT SETUP 

FONTS_DIR = r"C:\Windows\Fonts" 
FONT_MAP = {
    "Helvetica": "arial.ttf",
    "Helvetica-Bold": "arialbd.ttf",
}

def register_all_fonts():
    for font_name, file_name in FONT_MAP.items():
        font_path = os.path.join(FONTS_DIR, file_name)
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont(font_name, font_path))
        else:
            print(f"Warning: Font file not found: {font_path}") 

register_all_fonts()

# TEMPLATE SETTINGS

TEMPLATES = {
    "plain resume":{
        "primary": colors.HexColor("#2E2E2E"),
        "secondary": colors.HexColor("#4F4F4F"),
        "text": colors.black,
        "font_name": "Helvetica",
        "font_name_bold": "Helvetica-Bold",
        "font_sizes": {"title": 20, "header": 13, "body": 11},
        "spacing": {"section": 14, "paragraph": 5}
    }
}

# Validation functions

EMAIL_REGEX = r'^[\w\.-]+@[\w\.-]+\.\w+$'
def is_valid_email(email): return re.match(EMAIL_REGEX, email) is not None



def is_valid_email(email: str) -> bool:
    return re.match(EMAIL_REGEX, email or "") is not None

def is_valid_phone(phone: str) -> bool:
    phone = (phone or "").strip()


    if not re.match(r'^\+?[\d\s-]+$', phone):
        return False
    


    digits_only = re.sub(r'\D', '', phone)
    
    # Require 10–15 digits
    
    return 10 <= len(digits_only) <= 15

# TEXT WRAPPING

def wrap_text_dynamic(c, text, font_name, font_size, max_width):
    c.setFont(font_name, font_size)
    lines = []
    for paragraph in text.split("\n"):
        if not paragraph.strip():
            lines.append("")
            continue
        words = paragraph.split(" ")
        line = ""
        for word in words:
            if c.stringWidth((line + " " + word).strip(), font_name, font_size) <= max_width:
                line = (line + " " + word).strip()
            else:
                lines.append(line)
                line = word
        if line:
            lines.append(line)
    return lines

# PAGE HANDLING LOGIC

def ensure_space(c, y, needed, height, margin):
    """If not enough vertical space remains, start a new page"""
    if y - needed < margin:
        c.showPage()
        register_all_fonts()  
        return height - margin 
    return y


def draw_resume(c, style, data):
    width, height = A4
    margin = 50

    font_name = style["font_name"]
    font_bold = style["font_name_bold"]

    title_size = style["font_sizes"]["title"]
    header_size = style["font_sizes"]["header"]
    body_size = style["font_sizes"]["body"]
    section_gap = style["spacing"]["section"]
    paragraph_gap = style["spacing"]["paragraph"]



    y = height - margin

    # Name

    c.setFont(font_bold, title_size)
    c.setFillColor(style["primary"])
    c.drawCentredString(width / 2, y, data["full_name"].upper())
    y -= title_size + 8

    # Job Role

    if data["job_role"]:
        c.setFont(font_name, header_size)
        c.setFillColor(style["secondary"])
        c.drawCentredString(width / 2, y, data["job_role"])
        y -= header_size + 15

    # Contact Info

    c.setFont(font_name, body_size)
    c.setFillColor(style["text"])
    contact_line = f"{data['phone']}  |  {data['email']}"
    c.drawCentredString(width / 2, y, contact_line)
    y -= body_size + (section_gap * 2)

    # Sections

    sections = [
        ("Profile Summary", data["profile_summary"]),
        ("Work Experience", data["work_experience"]),
        ("Education", data["education"]),
        ("Skills", data["skills"]),
        ("Languages", data["languages"]),
        ("Certifications", data["certifications"]),

        # ("Awards", data["awards"]),

        ("Interests", data["interests"])
    ]

    for title, content in sections:
        if not content:
            continue



        c.setFont(font_bold, header_size)
        c.setFillColor(style["primary"])
        needed_height = header_size + paragraph_gap
        y = ensure_space(c, y, needed_height, height, margin) # Update y with returned value
        c.drawString(margin, y, title.upper())
        y -= header_size + (paragraph_gap * 2)



        c.setFont(font_name, body_size)
        c.setFillColor(style["text"])
        lines = wrap_text_dynamic(c, content, font_name, body_size, width - 2 * margin)
        for line in lines:
            needed_height = body_size + paragraph_gap
            y = ensure_space(c, y, needed_height, height, margin) # Update y with returned value
            c.drawString(margin, y, line)
            y -= body_size + paragraph_gap

        y -= section_gap

# Grammar tool

tool = language_tool_python.LanguageTool('en-US')

def auto_correct_text(text: str, skip_fields=()):
    if not text:
        return text

    if text in skip_fields:
        return text
    try:
        matches = tool.check(text)
        corrected = language_tool_python.utils.correct(text, matches)

   

        corrected = re.sub(r'([.!?]\s*)([a-z])', lambda m: m.group(1) + m.group(2).upper(), corrected)
        return corrected
    except Exception as e:
        print(f"Error during auto-correction: {e}") # Log correction errors
        return text

# API ENDPOINT


@app.post("/plain-resume")
async def generate_resume(data: ResumeData):

    # Validation

    if not data.full_name.strip() or not data.email.strip() or not data.phone.strip():
        raise HTTPException(status_code=400, detail="Name, Email and Phone are required")
    if not is_valid_email(data.email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    # Phone validation

    phone_cleaned = re.sub(r'[\s-]+', '', data.phone)
    if not phone_cleaned.isdigit() or len(phone_cleaned) != 10:
        raise HTTPException(status_code=400, detail="Invalid phone number format. Please enter a 10-digit number.")

    # Auto-correct longer fields

    data.job_role = auto_correct_text(data.job_role)

    profile_summary = auto_correct_text(data.profile_summary)
    education = auto_correct_text(data.education)
    skills = auto_correct_text(data.skills)
    work_experience = auto_correct_text(data.work_experience)
    certifications = auto_correct_text(data.certifications)
    interests = auto_correct_text(data.interests)
    languages = auto_correct_text(data.languages)

    resume_data = {
        "full_name": data.full_name,
        "job_role": data.job_role,
        "email": data.email,
        "phone": data.phone,
        "profile_summary": profile_summary,
        "work_experience": work_experience,
        "education": education,
        "skills": skills,
        "languages": languages,
        "certifications": certifications,

        # "awards": data.awards,

        "interests": interests,
    }

    # Create temp PDF
    temp_dir = tempfile.mkdtemp()
    file_name = f"{re.sub(r'\\W+', '_', data.full_name)}_{uuid.uuid4().hex[:8]}.pdf"
    file_path = os.path.join(temp_dir, file_name)

    try:
        c = canvas.Canvas(file_path, pagesize=A4)
        style = TEMPLATES['plain resume']
     
        draw_resume(c, style, resume_data)
        c.save()
    except HTTPException:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"PDF generation failed unexpectedly: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")

    return FileResponse(
        path=file_path,
        filename=file_name,
        media_type='application/pdf',
        background=BackgroundTask(shutil.rmtree, temp_dir, ignore_errors=True)
    )





