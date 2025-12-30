#!/bin/bash
# YouTube Queue Processor - Sequential execution only
# Alternates between LLaVA and LLaMA per video (not per frame)

QUEUE_FILE="/mnt/Wolf-code/Wolf-Ai-Enterptises/writers/analysis/youtube_queue.txt"
SCRIPT_DIR="/mnt/Wolf-code/Wolf-Ai-Enterptises/writers/analysis"
LOG_FILE="/tmp/youtube_queue_$(date +%Y%m%d_%H%M%S).log"

LLAVA_SCRIPT="$SCRIPT_DIR/youtube_analyst_llava.py"
LLAMA_SCRIPT="$SCRIPT_DIR/youtube_analyst_llama.py"

# Activate messiah environment
source ~/anaconda3/bin/activate messiah

echo "=============================================" | tee -a "$LOG_FILE"
echo "YouTube Queue Processor - ALTERNATING MODELS" | tee -a "$LOG_FILE"
echo "Odd videos: LLaVA 13b" | tee -a "$LOG_FILE"
echo "Even videos: LLaMA 3.2 Vision 11b" | tee -a "$LOG_FILE"
echo "Started: $(date)" | tee -a "$LOG_FILE"
echo "=============================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Process each URL one at a time, alternating models
line_num=0
total=$(wc -l < "$QUEUE_FILE")

while IFS= read -r url || [ -n "$url" ]; do
    # Skip empty lines
    [ -z "$url" ] && continue

    line_num=$((line_num + 1))

    # Alternate models per video
    if [ $((line_num % 2)) -eq 1 ]; then
        ANALYST_SCRIPT="$LLAVA_SCRIPT"
        MODEL_NAME="LLaVA 13b"
    else
        ANALYST_SCRIPT="$LLAMA_SCRIPT"
        MODEL_NAME="LLaMA 3.2 Vision 11b"
    fi

    echo "[$line_num/$total] Processing: $url" | tee -a "$LOG_FILE"
    echo "Model: $MODEL_NAME" | tee -a "$LOG_FILE"
    echo "Started at: $(date)" | tee -a "$LOG_FILE"

    # Run analyst - sequential, wait for completion
    python "$ANALYST_SCRIPT" "$url" --store --interval 15 2>&1 | tee -a "$LOG_FILE"

    exit_code=$?

    if [ $exit_code -eq 0 ]; then
        echo "✓ Complete: $url ($MODEL_NAME)" | tee -a "$LOG_FILE"
    else
        echo "✗ Failed: $url ($MODEL_NAME, exit code: $exit_code)" | tee -a "$LOG_FILE"
    fi

    echo "Finished at: $(date)" | tee -a "$LOG_FILE"
    echo "--------------------------------------------" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"

done < "$QUEUE_FILE"

echo "=============================================" | tee -a "$LOG_FILE"
echo "Queue processing complete" | tee -a "$LOG_FILE"
echo "Ended: $(date)" | tee -a "$LOG_FILE"
echo "Log saved: $LOG_FILE" | tee -a "$LOG_FILE"
echo "=============================================" | tee -a "$LOG_FILE"
