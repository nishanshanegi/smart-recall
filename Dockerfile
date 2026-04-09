# 1. Start with a lightweight Python image
FROM python:3.12-slim

# 2. Install Tesseract OCR and system dependencies
# WHY: Render's default environment doesn't have Tesseract. We must install it.
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    gcc \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 3. Set the working directory
WORKDIR /app

# 4. Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy your entire project code
COPY . .

# 6. Expose the port FastAPI runs on
EXPOSE 8000

# Default command (Render will override this for the worker)
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]