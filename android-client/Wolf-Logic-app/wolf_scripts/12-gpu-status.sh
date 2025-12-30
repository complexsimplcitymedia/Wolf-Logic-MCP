#!/bin/bash
# GPU status
if command -v rocm-smi &> /dev/null; then
    rocm-smi
elif command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,temperature.gpu,utilization.gpu,memory.used,memory.total --format=csv
else
    echo "No GPU tools found (rocm-smi or nvidia-smi)"
    echo "Checking for graphics..."
    lspci | grep -i vga
fi
