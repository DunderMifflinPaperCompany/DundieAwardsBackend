FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules
COPY shared/ shared/

# Copy service code
COPY services/notifications/ services/notifications/

# Expose port
EXPOSE 8004

# Run the service
CMD ["python", "services/notifications/main.py"]