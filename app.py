import os
import tempfile
import urllib.request
import subprocess
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import FileResponse

app = FastAPI()

# Output formats we support with Pandoc
PANDOC_FORMATS = [
    "pdf", "docx", "odt", "rtf", "md", "html", "txt",
    "tex", "epub", "asciidoc", "mediawiki"
]

# Map common file extensions to Pandoc input formats
EXT_TO_PANDOC = {
    "txt": "plain",
    "md": "markdown",
    "markdown": "markdown",
    "html": "html",
    "htm": "html",
    "docx": "docx",
    "odt": "odt",
    "rtf": "rtf",
    "tex": "latex",
    "csv": "csv",
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


@app.get("/health")
def health():
    return {
        "status": "OK",
        "uptime": os.times(),
        "supported": {
            "pandoc": True
        }
    }


@app.get("/formats")
def formats():
    return {
        "inputs": list(EXT_TO_PANDOC.keys()),
        "outputs": PANDOC_FORMATS,
        "notes": [
            "Pandoc is used exclusively for conversion.",
            "Input files must be UTF-8 text for text-based formats.",
            "PDF output may require LaTeX (already in Render image)."
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

    # Save input file to temp
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

        # Detect input format based on extension
        input_ext = os.path.splitext(input_name)[1].lower().strip(".")
        pandoc_from = EXT_TO_PANDOC.get(input_ext, "plain")

        # Attempt to re-encode text files to UTF-8 (to avoid decoding errors)
        if pandoc_from in ["plain", "markdown", "html", "latex", "asciidoc", "mediawiki", "csv"]:
            try:
                with open(tmp_input.name, "rb") as f:
                    raw = f.read()
                # Try common Windows encoding
                text = raw.decode("utf-8", errors="replace")
                with open(tmp_input.name, "w", encoding="utf-8") as f:
                    f.write(text)
            except Exception:
                pass  # Fail silently if not text-based

        # Prepare output file
        output_path = tempfile.NamedTemporaryFile(delete=False, suffix=f".{out_ext}").name

        # Run Pandoc
        try:
            subprocess.run(
                ["pandoc", "-f", pandoc_from, tmp_input.name, "-o", output_path],
                check=True
            )
        except subprocess.CalledProcessError as e:
            raise HTTPException(status_code=500, detail=f"Pandoc conversion failed: {e}")

        # Serve file
        filename = os.path.splitext(input_name)[0]
        final_name = f"{filename}.{out_ext}"
        return FileResponse(
            output_path,
            media_type="application/octet-stream",
            filename=final_name
        )

    finally:
        tmp_input.close()
