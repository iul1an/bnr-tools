FROM python:3.13-alpine

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the scripts
COPY bnr2telegram.py bnr_exporter.py ./

# Use non-root user for security
RUN adduser -D bnr
USER bnr

# Default environment variables
ENV LOG_LEVEL=INFO

# Expose Prometheus metrics port
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["python"]
