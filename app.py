import os
import tempfile
import urllib.request
import subprocess
import pathlib
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.requests import Request

app = FastAPI()

# Pandoc-supported output formats
PANDOC_FORMATS = [
    "pdf", "docx", "odt", "rtf", "md", "html", "txt",
    "tex", "epub", "asciidoc", "mediawiki"
]

# Map file extensions to Pandoc input formats
EXT_TO_PANDOC = {
    "txt": "markdown",   # treat txt as markdown-like
    "md": "markdown",
    "markdown": "markdown",
    "html": "html",
    "htm": "html",
    "docx": "docx",
    "odt": "odt",
    "rtf": "rtf",
    "tex": "latex",
    "csv": "markdown",
    "epub": "epub",
    "asciidoc": "asciidoc",
    "mediawiki": "mediawiki"
}


@app.get("/")
def home():
    return {
        "service": "Universal Document Converter API",
        "version": "1.0.0",
        "uptime": os.times()
    }


@app.head("/health")
@app.get("/health")
def health(request: Request):
    return JSONResponse({
        "status": "OK",
        "uptime": os.times(),
        "supported": {
            "pandoc": True
        }
    })


@app.get("/formats")
def formats():
    return {
        "inputs": list(EXT_TO_PANDOC.keys()),
        "outputs": PANDOC_FORMATS,
        "notes": [
            "Pandoc is used exclusively for conversion.",
            "Input files must be UTF-8 text for text-based formats.",
            "PDF output requires LaTeX (already installed in Docker)."
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

    # Normalize and validate output format
    out_ext = format.lower().strip(".")
    if out_ext not in PANDOC_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported output format '{out_ext}'. Supported: {', '.join(PANDOC_FORMATS)}"
        )

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

        # 🔸 Detect input format using pathlib
        ext_in = pathlib.Path(input_name).suffix.lower().strip(".")
        pandoc_from = EXT_TO_PANDOC.get(ext_in, "markdown")  # fallback to markdown

        # Attempt to re-encode text files to UTF-8
        if pandoc_from in ["plain", "markdown", "html", "latex", "asciidoc", "mediawiki", "csv"]:
            try:
                with open(tmp_input.name, "rb") as f:
                    raw = f.read()
                text = raw.decode("utf-8", errors="replace")
                with open(tmp_input.name, "w", encoding="utf-8") as f:
                    f.write(text)
            except Exception:
                pass

        # Prepare output file
        output_path = tempfile.NamedTemporaryFile(delete=False, suffix=f".{out_ext}").name

        # 🔸 Run Pandoc with detected input format
        try:
            subprocess.run(
                ["pandoc", "-f", pandoc_from, tmp_input.name, "-o", output_path],
                check=True
            )
        except subprocess.CalledProcessError as e:
            raise HTTPException(status_code=500, detail=f"Pandoc conversion failed: {e}")

        # Return converted file
        filename = os.path.splitext(input_name)[0]
        final_name = f"{filename}.{out_ext}"
        return FileResponse(
            output_path,
            media_type="application/octet-stream",
            filename=final_name
        )

    finally:
        tmp_input.close()
