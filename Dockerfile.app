FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install --no-install-recommends -y \
    curl \
    && rm -rf /var/lib/apt/lists/

RUN pip install --no-cache-dir \
    "uvicorn[standard]==0.34.0" httpx \
    python-multipart sse-starlette jinja2 \
    aiosqlite python-dotenv \
    pydantic pyyaml structlog fastapi==0.115.0 \
    pypdf python-docx beautifulsoup4 lxml \
    qdrant-client

COPY nexusclaw/ ./nexusclaw/
COPY web/dist/ ./web/dist/
COPY web/setup.html ./web/setup.html

EXPOSE 8000

CMD ["uvicorn", "nexusclaw.main:app", "--host", "0.0.0.0", "--port", "8000"]
