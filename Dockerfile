# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY pyproject.toml .
COPY README.md .

# Install the package in editable mode
RUN pip install -e .

# Set environment variables (will be overridden by docker-compose or runtime)
ENV FYTA_EMAIL=""
ENV FYTA_PASSWORD=""

# Run the MCP server
CMD ["python", "-m", "fyta_mcp_server.server"]
