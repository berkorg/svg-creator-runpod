#!/usr/bin/env bash

echo "Worker Initiated"

echo "Symlinking files from Network Volume"
ln -s /runpod-volume /workspace
rm -rf /root/.cache
ln -s /runpod-volume/.cache /root/.cache

echo "Starting RunPod Handler"
export PYTHONUNBUFFERED=1
cd /workspace/svg-creator-runpod
python3 -u rp_handler.py
