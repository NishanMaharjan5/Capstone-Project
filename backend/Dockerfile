FROM python:3.12-slim

# EasyOCR's PyTorch backend needs these even though we use opencv-python-headless
# (which itself skips the GUI libs a non-headless opencv would need).
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only the dependency manifest first so this layer stays cached across
# rebuilds unless requirements.txt itself changes — code edits below don't
# invalidate the (slow) pip install.
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout 300 --retries 10 -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
