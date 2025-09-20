# 1. Start with an official Python base image
# Using python:3.11-slim is a good choice for size and performance
FROM python:3.11-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy the requirements file first to leverage Docker's caching
COPY requirements.txt .

# 4. Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy your application code into the container
# This copies everything from your current directory into /app inside the container
# (respecting the .dockerignore file)
COPY . .

# 6. Expose the port the app runs on
# Uvicorn's default port is 8000
EXPOSE 8000

# 7. Define the command to run your app
# This is based on your command: "uvicorn src.main:app"
# We add --host 0.0.0.0 to make it accessible from outside the container
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]