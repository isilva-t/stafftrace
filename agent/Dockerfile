FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for PostgreSQL, ping, and networking
RUN apt-get update && apt-get install -y \
	postgresql-client \
	iputils-ping \
	gcc \
	python3-dev \
	arping \
	&& rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

CMD ["/app/entrypoint.sh"]
