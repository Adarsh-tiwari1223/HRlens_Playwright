FROM mcr.microsoft.com/playwright/python:v1.49.0-jammy

# Set working directory inside container
WORKDIR /app

# Set Python environment variables
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Copy requirements file first for layer caching optimization
COPY requirements.txt .

# Install Python dependencies (browsers pre-installed in Playwright base image)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source files
COPY . .

# Default command runs pytest (generic, easily overridden)
CMD ["pytest"]
