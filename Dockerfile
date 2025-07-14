# SecureCart AI Fraud Detection System - Docker Configuration
# Multi-stage Docker build for production deployment

# =============================================================================
# STAGE 1: Build Frontend (React Application)
# =============================================================================
FROM node:18-alpine AS frontend-builder

# Set working directory for frontend build
WORKDIR /app/frontend

# Copy package files first for better caching
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production --silent

# Copy frontend source code
COPY src/ ./src/
COPY public/ ./public/
COPY tsconfig.json ./
COPY .env* ./

# Build the React application
RUN npm run build

# =============================================================================
# STAGE 2: Build Backend Dependencies
# =============================================================================
FROM python:3.11-slim AS backend-deps

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies required for Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create application user (security best practice)
RUN useradd --create-home --shell /bin/bash app

# Set working directory
WORKDIR /app

# Copy requirements file
COPY backend/requirements.txt ./

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# =============================================================================
# STAGE 3: Production Image
# =============================================================================
FROM python:3.11-slim AS production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    PORT=5000

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    nginx \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Create application user
RUN useradd --create-home --shell /bin/bash app

# Create necessary directories
RUN mkdir -p /app/logs /app/models /app/static /var/log/supervisor

# Copy Python dependencies from deps stage
COPY --from=backend-deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-deps /usr/local/bin /usr/local/bin

# Copy built frontend from frontend-builder stage
COPY --from=frontend-builder /app/frontend/build /app/static/

# Set working directory
WORKDIR /app

# Copy backend source code
COPY backend/ ./backend/
COPY .env* ./

# Copy configuration files
COPY docker/nginx.conf /etc/nginx/nginx.conf
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY docker/entrypoint.sh /entrypoint.sh

# Make entrypoint script executable
RUN chmod +x /entrypoint.sh

# Change ownership of app directory to app user
RUN chown -R app:app /app /var/log/supervisor

# Create health check script
RUN echo '#!/bin/bash\ncurl -f http://localhost:$PORT/health || exit 1' > /healthcheck.sh && \
    chmod +x /healthcheck.sh

# Switch to non-root user
USER app

# Expose port
EXPOSE 5000 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD /healthcheck.sh

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Default command
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]

# =============================================================================
# DEVELOPMENT IMAGE (Alternative target)
# =============================================================================
FROM python:3.11-slim AS development

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=development \
    DEBUG=True

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    git \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Create application user
RUN useradd --create-home --shell /bin/bash app

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY backend/requirements.txt ./
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install pytest pytest-cov black flake8 mypy

# Copy source code
COPY backend/ ./backend/
COPY .env* ./

# Change ownership
RUN chown -R app:app /app

# Switch to non-root user
USER app

# Expose port
EXPOSE 5000

# Command for development
CMD ["python", "backend/app.py"]
