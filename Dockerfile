FROM node:18-slim

# Install LibreOffice + dependencies
RUN apt-get update && \
    apt-get install -y libreoffice && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .

EXPOSE 3000
CMD ["npm", "start"]
