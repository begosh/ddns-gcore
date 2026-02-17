FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY gcore_ddns.py .

# Default command
ENTRYPOINT ["python", "gcore_ddns.py"]
