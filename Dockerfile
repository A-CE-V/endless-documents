FROM python:3.11-bullseye

# Install LibreOffice, Pandoc, and extra fonts
RUN apt-get update && \
    apt-get install -y --no-install-recommends apt-utils && \
    apt-get install -y \
      libreoffice \
      pandoc \
      fonts-dejavu \
      fonts-liberation \
      fonts-noto \
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

# Expose port (use Render's $PORT in CMD)
EXPOSE 10000

# Start FastAPI using uvicorn with dynamic port
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
