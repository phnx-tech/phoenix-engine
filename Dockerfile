FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for Playwright and build tools.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# Copy the package source and install it.
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir -e .

# Install Playwright Chromium browser and its system dependencies.
RUN python -m playwright install chromium \
    && python -m playwright install-deps chromium

# Default entrypoint is the Phoenix CLI.
ENTRYPOINT ["phoenix"]
CMD ["--help"]
