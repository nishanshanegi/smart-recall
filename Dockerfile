# 1. Use an even smaller base image
FROM python:3.12-slim

# 2. Install dependencies and CLEAN UP in the same command
# WHY: In Docker, every 'RUN' creates a layer. If we delete junk in a separate RUN, 
# it stays in the previous layer. We must delete it in the SAME line.
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# 3. Use the CPU-only version of Torch (Crucial for size!)
COPY requirements.txt .
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]