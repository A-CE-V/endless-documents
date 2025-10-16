import os
import tempfile
import urllib.request
import subprocess
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import FileResponse

app = FastAPI()

# Pandoc-supported output formats
PANDOC_FORMATS = [
    "pdf", "docx", "odt", "rtf", "md", "html", "txt",
    "tex", "epub", "asciidoc", "mediawiki"
]


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
            "libreoffice": True
        }
    }


@app.get("/formats")
def formats():
    return {
        "inputs": [
            "docx", "doc", "odt", "rtf", "txt", "md", "html", "epub",
            "pptx", "xlsx", "csv", "tex", "asciidoc", "mediawiki"
        ],
        "outputs": PANDOC_FORMATS,
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

    # Normalize and validate format
    ext = format.lower().strip(".")
    if ext not in PANDOC_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{ext}'. Supported formats: {', '.join(PANDOC_FORMATS)}"
        )

    # Save input file
    tmp_input = tempfile.NamedTemporaryFile(delete=False)
    try:
        if file:
            content = await file.read()
            tmp_input.write(content)
            tmp_input.flush()
            input_name = file.filename
        else:
            urllib.request.urlretrieve(url, tmp_input.name)
            input_name = os.path.basename(url)

        # Prepare output path
        output_path = tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}").name

        # Convert using Pandoc via subprocess
        try:
            subprocess.run(
                ["pandoc", tmp_input.name, "-o", output_path],
                check=True
            )
        except subprocess.CalledProcessError as e:
            raise HTTPException(status_code=500, detail=f"Pandoc conversion failed: {e}")

        filename = os.path.splitext(input_name)[0]
        final_name = f"{filename}.{ext}"

        return FileResponse(
            output_path,
            media_type="application/octet-stream",
            filename=final_name
        )
    finally:
        tmp_input.close()
