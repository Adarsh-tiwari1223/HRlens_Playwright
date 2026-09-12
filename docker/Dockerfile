# ==============================================================================
# HRlens Automation Test Suite — Enterprise Playwright Container
# ==============================================================================
FROM mcr.microsoft.com/playwright/python:v1.49.0-jammy

# Configure container working directory
WORKDIR /app

# Ensure non-buffered stdout, bytecode suppression, and module resolution
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    DEBIAN_FRONTEND=noninteractive \
    TZ=Etc/UTC

# Install GUI streaming stack: Xvfb, x11vnc, noVNC, websockify, fluxbox
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        xvfb \
        x11vnc \
        novnc \
        websockify \
        fluxbox \
        x11-utils && \
    ln -sf /usr/share/novnc/vnc.html /usr/share/novnc/index.html && \
    rm -rf /var/lib/apt/lists/*

# Layer Caching Optimization: copy and install dependencies first
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Ensure persistent output directories exist inside container
RUN mkdir -p /app/reports /app/logs /app/test-results

# Copy entrypoint script and ensure Linux line endings and execute permissions
COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN sed -i 's/\r$//' /usr/local/bin/entrypoint.sh && \
    chmod +x /usr/local/bin/entrypoint.sh

# Copy repository source code into container
COPY . .

# Set entrypoint and default command
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["pytest"]
