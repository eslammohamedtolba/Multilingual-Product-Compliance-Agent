# Use Python 3.11 slim image as base
FROM python:3.11-slim-buster

# Set working directory inside the container
WORKDIR /app

# Install system dependencies required for some Python packages (e.g., pandas, numpy)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    g++ \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file into the working directory
COPY requirements.txt .

# Upgrade pip and install Python dependencies with no cache
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the entire application code into the container
COPY . .

# Expose the port that the application will listen on
EXPOSE 8000

# Command to run the application when the container starts
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
