FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_PREFER_BINARY=1 \
    PYTHONUNBUFFERED=1

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Upgrade apt packages and install required dependencies
RUN apt update && \
    apt upgrade -y && \
    apt install -y \
      python3-dev \
      python3-pip \
      python3.10-venv \
      fonts-dejavu-core \
      rsync \
      git \
      jq \
      moreutils \
      aria2 \
      wget \
      curl \
      libglib2.0-0 \
      libsm6 \
      libgl1 \
      libxrender1 \
      libxext6 \
      ffmpeg \
      libgoogle-perftools-dev \
      procps && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean -y

# Install the models
WORKDIR /workspace
RUN mkdir -p /workspace/models/ESRGAN && \
    cd /workspace/models/ESRGAN && \
    # Download the official Real-ESRGAN models
    wget https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth && \
    wget https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.1/RealESRNet_x4plus.pth && \
    wget https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth && \
    wget https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth && \
    # Download additional models from Huggingface
    # wget https://huggingface.co/snappic/upscalers/resolve/main/4x-UltraSharp.pth && \
    # wget https://huggingface.co/snappic/upscalers/resolve/main/lollypop.pth && \
    # Download the GFPGAN models
    mkdir -p /workspace/models/GFPGAN && \
    wget -O /workspace/models/GFPGAN/GFPGANv1.3.pth https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.3.pth

# Install Torch
RUN pip3 install --no-cache-dir torch==2.0.1 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 1. Clone the worker repo
# 2. Install requirements
# 3. Setup the local requirements
# 4. Create test_input.json file for test inference
# 5. Run test inference using rp_handler.py to cache the models
RUN git clone https://github.com/berkorg/svg-creator-runpod.git && \
    cd svg-creator-runpod && \
    pip3 install -r requirements.txt && \
    python3 setup.py develop && \
    python3 create_test_json.py && \
    python3 -u rp_handler.py

# Docker container start script
ADD start_standalone.sh /start.sh
ADD rp_handler.py /workspace/svg-creator-runpod/rp_handler.py

# Start the container
RUN chmod +x /start.sh
ENTRYPOINT /start.sh
