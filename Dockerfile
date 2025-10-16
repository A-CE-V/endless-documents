FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libreoffice \
    unoconv \
    pandoc \
    fonts-dejavu \
    fonts-liberation \
    xfonts-base \
    xfonts-75dpi \
    xfonts-scalable \
    wget \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 10000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "10000"]
