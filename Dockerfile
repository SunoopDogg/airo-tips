FROM debian:trixie-slim

ENV DEBIAN_FRONTEND=noninteractive

# Update package lists
RUN apt update

# Core utilities
RUN apt install -y --no-install-recommends \
        ca-certificates \
        curl \
        unzip

# Git and Git LFS
RUN apt install -y --no-install-recommends \
        git \
        git-lfs \
    && git lfs install

# GUI / Rendering libraries
RUN apt install -y --no-install-recommends \
        libgl1 \
        libgtk2.0-dev \
        tk

# uv installation
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# nvm installation
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
ENV NVM_DIR=/root/.nvm
RUN . "$NVM_DIR/nvm.sh"

# Node.js for cadgen's mesh/DXF builders (text-to-cad plugin)
RUN . "$NVM_DIR/nvm.sh" \
    && nvm install 22 \
    && nvm alias default 22 \
    && ln -s "$(nvm which 22)" /usr/local/bin/node

# System libraries for cadgen's headless Chromium snapshot renderer
RUN /root/.local/bin/uvx --from playwright==1.63.0 playwright install-deps chromium-headless-shell

# Clean up
RUN apt clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /root