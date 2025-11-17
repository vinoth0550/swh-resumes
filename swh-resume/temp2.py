


# temp2.py -template 2 without banner section and added job role section

# this header changable template and data will be in body and raw json format

from reportlab.lib.utils import ImageReader

from fastapi import FastAPI, Form, File, UploadFile, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from reportlab.pdfgen import canvas
from typing import Optional
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import re, os, tempfile, uuid, shutil
import language_tool_python
   

###
from pydantic import BaseModel, Field
from typing import Optional

# Create a Pydantic model for the JSON request
class ResumeData(BaseModel):
    full_name: str

    job_role : str = ""      # new field
    
    email: str
    phone: str
    profile_summary: str = ""
    profile_summary_header: str = "Profile Summary"
    education: str = ""
    education_header: str = "Education"
    skills: str = ""
    skills_header: str = "Skills"
    work_experience: str = ""
    work_experience_header: str = "Work Experience"
    languages: str = ""
    languages_header: str = "Languages"
    certifications: str = ""
    certifications_header: str = "Certifications"
    interests: str = ""
    interests_header: str = "Interests"

###


app = FastAPI(title="Resume Builder API")

# Allow local browser access from any origin for testing

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Font detection & register

FONTS_DIR = r"C:\Windows\Fonts"

FONT_MAP = {
    "Arial": "arial.ttf",
    "Arial-Bold": "arialbd.ttf",
    "Calibri": "calibri.ttf",
    "Calibri-Bold": "calibrib.ttf",
    "Times-Roman": "times.ttf",
    "Times-Bold": "timesbd.ttf",
    "Cambria": "cambria.ttf",
    "Cambria-Bold": "cambriab.ttf",
    "Garamond": "garamond.ttf",
    "Garamond-Bold": "garamond-bold.ttf",
    "Georgia": "georgia.ttf",
    "Georgia-Bold": "georgiab.ttf",
    "Tahoma": "tahoma.ttf",
    "Tahoma-Bold": "tahomabd.ttf",
    "Verdana": "verdana.ttf",
    "Verdana-Bold": "verdanab.ttf",
    "TrebuchetMS": "trebuc.ttf",
    "TrebuchetMS-Bold": "trebucbd.ttf"
}



def register_all_fonts():
    for font_name, file_name in FONT_MAP.items():
        font_path = os.path.join(FONTS_DIR, file_name)
        if not os.path.exists(font_path):
            continue
        try:
            pdfmetrics.registerFont(TTFont(font_name, font_path))
        except Exception:
         
            pass

register_all_fonts()


# Templates definition

TEMPLATES = {
    
 "Modern Green": {
        "primary": colors.HexColor("#27AE60"),
        "secondary": colors.HexColor("#2ECC71"),
        "text": colors.HexColor("#333333"),
        "sidebar_bg": colors.HexColor("#ECF0F1"),
        "sidebar_width": 0.30,  # 0.25
        "font_name": "Calibri",
        "font_name_bold": "Calibri-Bold",

        "font_sizes": {"title": 22,  "job_role": 16, "header": 12, "body": 11}, # title = 18
        
        "spacing": {"section": 14, "paragraph": 5}
    }
}


# validation & text wrapping

EMAIL_REGEX = r'^[\w\.-]+@[\w\.-]+\.\w+$'

def is_valid_email(email: str) -> bool:
    return re.match(EMAIL_REGEX, email or "") is not None



def is_valid_phone(phone: str) -> bool:
    phone = (phone or "").strip()
    
    # Allow only digits, spaces, hyphens, and an optional +
    if not re.match(r'^\+?[\d\s-]+$', phone):
        return False
    
    # Remove non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    
    # Require 10–15 digits
    return 10 <= len(digits_only) <= 15

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

                # Force break for long unbreakable words (like email addresses)
                
                if c.stringWidth(word, font_name, font_size) > max_width:
                    subword = ""
                    for ch in word:
                        if c.stringWidth(subword + ch, font_name, font_size) <= max_width:
                            subword += ch
                        else:
                            if subword:
                                lines.append(subword)
                            subword = ch
                    if subword:
                        line = subword
                    else:
                        line = ""
                else:
                    if line:
                        lines.append(line)
                    line = word
        if line:
            lines.append(line)
    return lines



# PDF generation functions


def draw_resume(c, style, data, banner_path: Optional[str] = None):

#
    printed_sidebar_headers = set()
    printed_main_headers = set()
#

    width, height = A4
    margin = 40
    bottom_margin = 0
    sidebar_width = width * style["sidebar_width"]
    font_name = style["font_name"]
    font_name_bold = style["font_name_bold"]
    if font_name not in pdfmetrics.getRegisteredFontNames():
        font_name = "Helvetica"
    if font_name_bold not in pdfmetrics.getRegisteredFontNames():
        font_name_bold = "Helvetica-Bold"
    title_size = style["font_sizes"]["title"]
    header_size = style["font_sizes"]["header"]
    body_size = style["font_sizes"]["body"]
    section_gap = style["spacing"]["section"]
    paragraph_gap = style["spacing"]["paragraph"]

    def start_new_page():
        c.showPage()

        # For subsequent pages, no banner space — draw sidebar background full height

        c.setFillColor(style["sidebar_bg"])
        c.rect(0, 0, sidebar_width, height, fill=True, stroke=False)
        return height - margin - 0   ###


    def draw_content(y_position, sidebar_data, main_data, start_sidebar_idx=0, start_main_idx=0, start_sidebar_line=0, start_main_line=0):
        sx = margin / 2
        mx = sidebar_width + margin
        sidebar_y = y_position
        main_y = y_position
        max_content_height = y_position - bottom_margin


        ###

        if start_sidebar_idx == 0 and start_main_idx == 0:
            # Draw full name
            c.setFont(font_name_bold, title_size)
            c.setFillColor(style["primary"])
            c.drawString(mx, main_y, (data.get("full_name") or "").upper())
            main_y -= title_size + 2  # Smaller gap between name and job role        #5
            
            # Draw job role if provided
            if data.get("job_role"):
                job_role_size = style["font_sizes"].get("job_role", header_size)
                
                # Draw highlighted background for job role
                job_role = data.get("job_role", "")
                job_role_width = c.stringWidth(job_role, font_name, job_role_size)
                

                
                # Draw job role text

                c.setFillColor(colors.HexColor("#27AE60"))  # White text for contrast


                c.setFont(font_name_bold, job_role_size)
                c.drawString(mx, main_y, job_role)
                
                main_y -= (job_role_size + section_gap + 5)  # Add extra space after job role
            else:
                main_y -= section_gap  # Normal spacing if no job role

        ###



        sidebar_idx = start_sidebar_idx
        main_idx = start_main_idx
        sidebar_line = start_sidebar_line
        main_line = start_main_line
        sidebar_lines = {}
        main_lines = {}

     


        #

        for i, section in enumerate(sidebar_data):
            content_key = section["content"]  # Get the content key (e.g., "skills")
            if data.get(content_key):
                sidebar_lines[i] = wrap_text_dynamic(c, data[content_key], font_name, body_size, sidebar_width - sx - 10)
                
        for i, section in enumerate(main_data):
            content_key = section["content"]  # Get the content key (e.g., "profile_summary") 
            if data.get(content_key):
                main_lines[i] = wrap_text_dynamic(c, data[content_key], font_name, body_size, width - sidebar_width - 2 * margin)

        #

        while sidebar_idx < len(sidebar_data) or main_idx < len(main_data):
            drew_anything = False  # Track if we wrote anything this cycle

            #  SIDEBAR SECTION 
            if sidebar_idx < len(sidebar_data):
                content_key = sidebar_data[sidebar_idx]["content"]
                if data.get(content_key):



                    ##
                   
                    header_text = sidebar_data[sidebar_idx]["header"]
                    if sidebar_line == 0 and header_text not in printed_sidebar_headers:
                            if sidebar_y - (header_size + section_gap) <= bottom_margin:
                                break
                            c.setFont(font_name_bold, header_size)
                            c.setFillColor(style["primary"])
                            c.drawString(sx, sidebar_y, header_text.upper())
                            sidebar_y -= header_size + section_gap
                            printed_sidebar_headers.add(header_text)

                   
                   ##




                    if sidebar_line < len(sidebar_lines.get(sidebar_idx, [])):
                        if sidebar_y - (body_size + paragraph_gap) <= bottom_margin:
                            break
                        c.setFont(font_name, body_size)
                        c.setFillColor(style["text"])
                        line = sidebar_lines[sidebar_idx][sidebar_line]
                        c.drawString(sx, sidebar_y, line)
                        sidebar_y -= body_size + paragraph_gap
                        sidebar_line += 1
                        drew_anything = True

                    # Section finished
                    if sidebar_line >= len(sidebar_lines.get(sidebar_idx, [])):
                        sidebar_line = 0
                        sidebar_idx += 1
                        if sidebar_idx < len(sidebar_data):
                            sidebar_y -= section_gap

            #  MAIN SECTION 
            if main_idx < len(main_data):
                content_key = main_data[main_idx]["content"]
                if data.get(content_key):

                ##

                    header_text = main_data[main_idx]["header"]
                    if main_line == 0 and header_text not in printed_main_headers:
                        if main_y - (header_size + section_gap) <= bottom_margin:
                            break
                        c.setFont(font_name_bold, header_size)
                        c.setFillColor(style["primary"])
                        c.drawString(mx, main_y, header_text.upper())
                        main_y -= header_size + section_gap
                        printed_main_headers.add(header_text)

                ##
            

                    if main_line < len(main_lines.get(main_idx, [])):
                        if main_y - (body_size + paragraph_gap) <= bottom_margin:
                            break
                        c.setFont(font_name, body_size)
                        c.setFillColor(style["text"])
                        line = main_lines[main_idx][main_line]
                        c.drawString(mx, main_y, line)
                        main_y -= body_size + paragraph_gap
                        main_line += 1
                        drew_anything = True

                    if main_line >= len(main_lines.get(main_idx, [])):
                        main_line = 0
                        main_idx += 1
                        if main_idx < len(main_data):
                            main_y -= section_gap

            # Stop loop if nothing drawn

            if not drew_anything:
                break

        # Track lowest Y position

        y_position = min(sidebar_y, main_y)
        return y_position, sidebar_idx, sidebar_line, main_idx, main_line



    # Draw sidebar background FIRST (full height including banner area)

    c.setFillColor(style["sidebar_bg"])
    c.rect(0, 0, sidebar_width, height, fill=True, stroke=False)

    # Then draw the banner (so it sits ON TOP of the sidebar)

    y_position_top = height - margin
    banner_drawn_height = 0


    # Adjust Y position below the banner

    y_position = height - banner_drawn_height - margin



    

    sidebar_sections = [
        {"content": "email", "header": "email"}, 
        {"content": "phone", "header": "phone"},
        {"content": "skills", "header": data.get("skills_header", "Skills")},
        {"content": "languages", "header": data.get("languages_header", "Languages")},
        {"content": "certifications", "header": data.get("certifications_header", "Certifications")}
    ]

    main_sections = [
        
        {"content": "profile_summary", "header": data.get("profile_summary_header", "Profile Summary")},
        {"content": "work_experience", "header": data.get("work_experience_header", "Work Experience")},
        {"content": "education", "header": data.get("education_header", "Education")},
        {"content": "interests", "header": data.get("interests_header", "Interests")}
    ]

#
    sidebar_idx = main_idx = sidebar_line = main_line = 0
    while sidebar_idx < len(sidebar_sections) or main_idx < len(main_sections):
        y_position, sidebar_idx, sidebar_line, main_idx, main_line = draw_content(
            y_position, sidebar_sections, main_sections, sidebar_idx, main_idx, sidebar_line, main_line
        )
        if sidebar_idx < len(sidebar_sections) or main_idx < len(main_sections):
            y_position = start_new_page()


# Grammar tool (server-side auto-correct)

tool = language_tool_python.LanguageTool('en-US')

def auto_correct_text(text: str, skip_fields=()):
    if not text:
        return text
    
    # Do not run correction on certain short fields

    if text in skip_fields:
        return text
    try:
        matches = tool.check(text)
        corrected = language_tool_python.utils.correct(text, matches)
        corrected = re.sub(r'([^\w\s]\s*)([a-z])', lambda m: m.group(1) + m.group(2).upper(), corrected)
        return corrected
    except Exception:
        return text


###
@app.post("/Modern-Green")
async def generate(data: ResumeData):


    # banner: Optional[UploadFile] = File(None)


    # Validation
    if not data.full_name.strip() or not data.email.strip() or not data.phone.strip():
        raise HTTPException(status_code=400, detail="Name, Email and Phone are required")
    if not is_valid_email(data.email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    if not is_valid_phone(data.phone):
        raise HTTPException(status_code=400, detail="Invalid phone no, Enter valid Number")

    # Auto-correct longer fields

    data.job_role = auto_correct_text(data.job_role)
    data.profile_summary = auto_correct_text(data.profile_summary)
    data.education = auto_correct_text(data.education)
    data.skills = auto_correct_text(data.skills)
    data.work_experience = auto_correct_text(data.work_experience)
    data.certifications = auto_correct_text(data.certifications)
    data.interests = auto_correct_text(data.interests)
    data.languages = auto_correct_text(data.languages)

    resume_data = {
        'full_name': data.full_name.strip(),
        
        'job_role': data.job_role.strip(),  # Added job_role

        'email': data.email.strip(),
        'phone': data.phone.strip(),
        'profile_summary': data.profile_summary.strip(),
        'profile_summary_header': data.profile_summary_header.strip(),
        'education': data.education.strip(),
        'education_header': data.education_header.strip(),
        'skills': data.skills.strip(),
        'skills_header': data.skills_header.strip(),
        'work_experience': data.work_experience.strip(),
        'work_experience_header': data.work_experience_header.strip(),
        'languages': data.languages.strip(),
        'languages_header': data.languages_header.strip(),
        'certifications': data.certifications.strip(),
        'certifications_header': data.certifications_header.strip(),
        'interests': data.interests.strip(),
        'interests_header': data.interests_header.strip()
    }

###



###

    # Create temp PDF (and optionally banner image)
    temp_dir = tempfile.mkdtemp()
    file_name = f"{re.sub(r'\\W+', '_', data.full_name)}_{uuid.uuid4().hex[:8]}.pdf"
    file_path = os.path.join(temp_dir, file_name)


###


    try:
        c = canvas.Canvas(file_path, pagesize=A4)
        style = TEMPLATES['Modern Green']
        draw_resume(c, style, resume_data, banner_path=None)
        c.save()

    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")

    return FileResponse(path=file_path, filename=file_name, media_type='application/pdf')





