# Gift AI Service Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Pillow for image processing
RUN pip install --no-cache-dir Pillow

# Copy service code
COPY . .

# Cloud Run uses PORT env var
ENV PORT=8080
EXPOSE 8080

# Run application
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT} --workers 1