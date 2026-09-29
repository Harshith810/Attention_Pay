FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# System packages required by Python dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libgomp1 \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy Docker-specific Python dependencies
COPY backend/requirements-docker.txt ./requirements-docker.txt

# Install CPU-only PyTorch
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir \
        --index-url https://download.pytorch.org/whl/cpu \
        torch

# Install remaining dependencies
RUN pip install --no-cache-dir -r requirements-docker.txt

# Copy backend application
COPY backend ./backend

# Copy BERT model
COPY model ./model

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]