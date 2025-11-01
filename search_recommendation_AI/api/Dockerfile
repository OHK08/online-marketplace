FROM python:3.11-slim

WORKDIR /app

# Install build tools (lightweight, then cleaned)
RUN apt-get update -y \
 && apt-get install -y --no-install-recommends build-essential curl \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./

# Use constraints to ensure dependency stability
RUN pip install --upgrade pip setuptools wheel \
 && pip install --no-cache-dir -r requirements.txt 

COPY . .

ENV PORT=8080
EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
