FROM node:18-bullseye

# Install LibreOffice + dependencies + fonts
RUN apt-get update && \
    apt-get install -y \
      libreoffice \
      libreoffice-writer \
      libreoffice-calc \
      libreoffice-impress \
      libreoffice-common \
      fonts-dejavu \
      fonts-liberation \
      xfonts-base \
      xfonts-75dpi \
      xfonts-scalable \
      unzip \
      wget \
      curl \
      unoconv \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Symlink soffice so libreoffice-convert can find it
RUN ln -s /usr/lib/libreoffice/program/soffice /usr/bin/soffice || true

# App setup
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .

EXPOSE 3000
CMD ["npm", "start"]
