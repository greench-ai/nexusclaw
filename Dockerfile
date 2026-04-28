FROM python:3.12-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for caching)
COPY requirements.txt .

# Install Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright (optional)
RUN pip install --no-cache-dir playwright \
    && python -m playwright install chromium --with-deps 2>/dev/null || true

# Copy app
COPY . .

# Create nexusclaw user dir
RUN mkdir -p /root/.nexusclaw

# Expose ports
EXPOSE 8080 19789

# Default: start API
CMD ["python", "apps/api/main.py"]
