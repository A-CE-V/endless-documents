# Use a lightweight base with Python and apt support
FROM python:3.11-bullseye

# Prevent interactive prompts during installs
ENV DEBIAN_FRONTEND=noninteractive

# Install required system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    apt-utils \
    curl \
    wget \
    libreoffice \
    unoconv \
    pandoc \
    texlive-xetex \
    texlive-fonts-recommended \
    texlive-latex-base \
    texlive-latex-extra \
    texlive-plain-generic \
    fonts-dejavu \
    fonts-liberation \
    fonts-freefont-ttf \
    fonts-lmodern \
    xfonts-base \
    xfonts-75dpi \
    xfonts-scalable \
    xvfb \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the app port
EXPOSE 10000

# Run the app with Uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "10000"]
