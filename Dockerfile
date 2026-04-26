FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y \
    curl git nodejs npm \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY pyproject.toml requirements.txt* ./
RUN pip install --no-cache-dir -r requirements.txt 2>/dev/null || true

# Copy source
COPY . .

# Download Ollama (optional)
RUN if command -v curl; then \
    curl -fsSL https://ollama.com/install.sh | sh; \
    fi

EXPOSE 8080 51234

# Default: run API
CMD ["python3", "apps/api/main.py"]
