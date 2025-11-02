# Gift AI Service Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libglib2.0-0 libsm6 libxext6 libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency list first for layer caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir Pillow uvicorn

# Copy source code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PORT=8080

# Expose port
EXPOSE 8080

# Launch the service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
