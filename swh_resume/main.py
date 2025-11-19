

import uuid
import inspect
import os
import shutil
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from temp1 import generate as template1
from temp2 import generate as template2
from temp3 import generate as template3
from temp4 import generate as template4
from temp5 import generate as template5
from temp6 import generate_resume as template6
from temp7 import generate_resume as template7

app = FastAPI()

# Allowing all origins for frontend

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create resume-pdfs folder AUTOMATICALLY
PDF_FOLDER = "resume-pdfs"
os.makedirs(PDF_FOLDER, exist_ok=True)

# Serve files for download
app.mount("/files", StaticFiles(directory=PDF_FOLDER), name="files")

# Convert dict → object for your template code
class Obj:
    def __init__(self, d):
        for k, v in d.items():
            setattr(self, k, v)

# Track current template index
current_template_index = 0

templates = [
    template1,
    template2,
    template3,
    template4,
    template5,
    template6,
    template7,
]

@app.post("/resume")
async def unified_resume(data: dict):
    global current_template_index

    # Stop after 7 templates
    if current_template_index >= len(templates):
        return {"message": "All templates finished", "last_template": True}

    selected_template = templates[current_template_index]
    template_number = current_template_index + 1
    current_template_index += 1

    try:
        obj = Obj(data)

        # Run async or sync template
        if inspect.iscoroutinefunction(selected_template):
            response = await selected_template(obj)
        else:
            response = selected_template(obj)

        # FileResponse has .path where PDF is stored
        source_file_path = response.path

        # Standard output name 

    
        unique = uuid.uuid4().hex[:4].upper()
        final_pdf_name = f"template_{template_number}_{unique}.pdf"


        # final_pdf_name = f"template_{template_number}.pdf"
        final_pdf_path = os.path.join(PDF_FOLDER, final_pdf_name)

        # Copy or overwrite file in resume-pdfs
        shutil.copy(source_file_path, final_pdf_path)

        # Return JSON instead of PDF
        return {
            "status": "success",
            "message": f"Resume template {template_number} has been created successfully!",
            "download_link": f"http://127.0.0.1:8000/files/{final_pdf_name}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
  