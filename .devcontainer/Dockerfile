FROM python:3.11-slim

# Set up a non-root user
RUN useradd -ms /bin/bash vscode
USER vscode
WORKDIR /workspace

# Install system dependencies
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    portaudio19-dev \
    libsndfile1-dev \
    sox \
    && rm -rf /var/lib/apt/lists/*
USER vscode

# Copy and install python requirements
COPY --chown=vscode:vscode requirements.txt .
RUN pip install --user -r requirements.txt

# Add user's local bin to path
ENV PATH="/home/vscode/.local/bin:${PATH}"
