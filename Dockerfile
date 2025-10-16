FROM python:3.11-bullseye

# Install system dependencies: LibreOffice, Pandoc, LaTeX, fonts, unoconv
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      apt-utils \
      libreoffice \
      unoconv \
      pandoc \
      texlive-xetex \
      texlive-fonts-recommended \
      texlive-plain-generic \
      fonts-dejavu \
      fonts-liberation \
      xfonts-base \
      xfonts-75dpi \
      xfonts-scalable \
      wget \
      curl && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose API port
EXPOSE 10000

# Start the FastAPI server
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "10000"]
