FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules
COPY shared/ shared/

# Copy service code
COPY services/security/ services/security/

# Expose port
EXPOSE 8005

# Run the service
CMD ["python", "services/security/main.py"]