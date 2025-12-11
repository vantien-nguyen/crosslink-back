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
    APP_DIR=/app \
    WORKER_SCRIPT=/start-worker

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
COPY ./deployment/local/worker/start ${WORKER_SCRIPT}
RUN sed -i 's/\r$//' ${WORKER_SCRIPT} && chmod +x ${WORKER_SCRIPT}

# Set the working directory to the Django project root
WORKDIR ${APP_DIR}/crosslink
CMD ["/bin/sh", "/start-worker"]
