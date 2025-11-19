

import uuid
import inspect
import os
import shutil
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from templates import templates   # ← from templates.py

app = FastAPI()

# CORS (for browser + Postman)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Folder to store final PDFs
PDF_FOLDER = "resume-pdfs"
os.makedirs(PDF_FOLDER, exist_ok=True)

# Serve the saved PDF files
app.mount("/files", StaticFiles(directory=PDF_FOLDER), name="files")


# Convert body -> object with attributes (like your old code)
class Obj:
    def __init__(self, d):
        for k, v in d.items():
            setattr(self, k, v)


# Track current template index
current_template_index = 0


@app.post("/resume")
async def unified_resume(data: dict):
    """
    Runs templates 1 to N sequentially.
    Each request returns the next template's output.
    """
    global current_template_index

    # Stop after finishing all templates
    if current_template_index >= len(templates):
        return {"message": "All templates finished", "last_template": True}

    template_fn = templates[current_template_index]
    template_number = current_template_index + 1
    current_template_index += 1

    try:
        # # Convert incoming json to object
        # obj = Obj(data)

        # # Call template (sync or async)
        # if inspect.iscoroutinefunction(template_fn):
        #     response = await template_fn(obj)
        # else:
        #     response = template_fn(obj)


        obj = Obj(data)
        data_dict = obj.__dict__      # convert to dictionary

        if inspect.iscoroutinefunction(template_fn):
            response = await template_fn(data_dict)
        else:
            response = template_fn(data_dict)


        # Extract temporary PDF path from FileResponse
        source_file_path = response.path

        # Unique name
        code = uuid.uuid4().hex[:4].upper()
        final_name = f"template_{template_number}_{code}.pdf"
        final_path = os.path.join(PDF_FOLDER, final_name)

        # Copy PDF into final folder
        shutil.copy(source_file_path, final_path)

        return {
            "status": "success",
            "template_number": template_number,
            "message": f"Template {template_number} generated successfully",
            "download_link": f"http://127.0.0.1:8000/files/{final_name}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
