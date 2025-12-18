FROM python:3.13-slim

# Prevent Python buffering & pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set workdir
WORKDIR /app

# System deps (bcrypt, httpx, uvloop stability)
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose port (Render ignores this but good practice)
EXPOSE 8000

# Start FastAPI (Render overrides PORT)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]