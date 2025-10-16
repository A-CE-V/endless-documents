import os
import tempfile
import urllib.request
import pypandoc
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import FileResponse

app = FastAPI()


@app.get("/")
def home():
    return {
        "service": "Universal Document Converter API",
        "version": "1.0.0",
        "uptime": os.times()
    }

@app.get("/health")
def health():
    return {
        "status": "OK",
        "uptime": os.times(),
        "supported": {
            "pandoc": True,
            "libreoffice": True  # Still installed but fallback is skipped
        }
    }

@app.get("/formats")
def formats():
    return {
        "inputs": [
            "docx", "doc", "odt", "rtf", "txt", "md", "html", "epub",
            "pptx", "xlsx", "csv", "tex", "asciidoc", "mediawiki"
        ],
        "outputs": [
            "pdf", "docx", "odt", "rtf", "md", "html", "txt",
            "pptx", "xlsx", "csv", "tex", "epub", "asciidoc", "mediawiki"
        ],
        "notes": [
            "Pandoc is used exclusively for conversion.",
            "LibreOffice is installed but fallback is disabled.",
            "PDF output may require LaTeX for some formats."
        ]
    }

@app.post("/convert")
async def convert_file(
    format: str = Form(...),
    file: UploadFile = File(None),
    url: str = Form(None)
):
    if not file and not url:
        raise HTTPException(status_code=400, detail="No file or URL provided")

    # Save input file
    tmp_input = tempfile.NamedTemporaryFile(delete=False)
    if file:
        content = await file.read()
        tmp_input.write(content)
        tmp_input.flush()
        input_name = file.filename
    else:
        try:
            urllib.request.urlretrieve(url, tmp_input.name)
            input_name = os.path.basename(url)
        except Exception:
            raise HTTPException(status_code=400, detail="Could not download file from URL")

    # Prepare output path
    ext = format.lower().strip(".")
    output_path = tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}").name

    # Pandoc-only conversion
    try:
        pypandoc.convert_file(tmp_input.name, to=ext, outputfile=output_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pandoc conversion failed: {e}")

    filename = os.path.splitext(input_name)[0]
    final_name = f"{filename}.{ext}"

    return FileResponse(
        output_path,
        media_type="application/octet-stream",
        filename=final_name
    )
