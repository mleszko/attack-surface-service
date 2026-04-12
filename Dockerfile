# Dockerfile for Attack Surface Service
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Run app from the package directory so local imports resolve.
WORKDIR /app/app

# Expose default port
EXPOSE 80

# Set environment variable at runtime or via .env
# ENV ENV_PATH=tests/cloud.json

# Run the application
CMD ["uvicorn", "attack_surface:app", "--host", "0.0.0.0", "--port", "80"]
