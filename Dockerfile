FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    tesseract-ocr \
    tesseract-ocr-eng \
    python3-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create necessary directories
RUN mkdir -p uploads results mock_ams

# Copy requirements first
COPY requirements.txt .

# Install Python dependencies with explicit gunicorn installation
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir gunicorn==20.1.0 && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
# Note: PORT will be overridden by Railway to 8080
ENV PORT=8080

# Expose port
EXPOSE 8080

# Start the application - use $PORT to respect Railway's setting
CMD cd src && python -m gunicorn main:app --bind 0.0.0.0:$PORT --timeout 300 