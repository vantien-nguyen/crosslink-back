###################
### Build stage ###
###################
FROM python:3.11-alpine AS build

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/venv \
    PATH="/venv/bin:$PATH" \
    APP_DIR=/app

# Install required build dependencies
RUN apk add --no-cache build-base libpq postgresql-dev

# Create virtual environment & install dependencies
RUN python -m venv ${VIRTUAL_ENV} && \
    pip install --upgrade pip && \
    pip install poetry

# Set working directory and install Python dependencies
WORKDIR ${APP_DIR}
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root && \
    rm -rf /root/.cache/pip && \
    find ${VIRTUAL_ENV} -name '__pycache__' -exec rm -r {} + && \
    apk del build-base postgresql-dev  # Remove build tools

# Copy only necessary app files
COPY . .

#####################
### Runtime stage ###
#####################
FROM python:3.11-alpine AS runtime

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/venv \
    PATH="/venv/bin:$PATH" \
    APP_DIR=/app

# Install only runtime dependencies
RUN apk add --no-cache libpq bash

# Set working directory
WORKDIR ${APP_DIR}

# Copy virtual environment and app code
COPY --from=build ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY --from=build ${APP_DIR} ${APP_DIR}

# Optimize binary size
RUN strip --strip-unneeded /venv/bin/* || true

# Prepare entrypoint
COPY ./deployment/local/backend/entrypoint.sh /entrypoint.sh
COPY ./deployment/local/backend/start /start
RUN sed -i 's/\r$//' /entrypoint.sh /start && chmod +x /entrypoint.sh /start

# Expose port and set entrypoint
EXPOSE 8000
CMD ["/bin/sh", "/entrypoint.sh"]
