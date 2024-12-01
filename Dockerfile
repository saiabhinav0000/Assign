FROM python:3.7-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY services/ ./services/

# Make the application externally accessible
ENV PORT=8080
ENV HOST=0.0.0.0
ENV MONGODB_URI="mongodb+srv://mongo:ipW272wjb1fwWRSi@cluster0.efff1.mongodb.net/?retryWrites=true&w=majority"

# Run the API Gateway service
CMD ["python", "services/api_gateway/apiv1.py"]