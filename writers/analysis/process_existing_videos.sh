#!/bin/bash
# Process existing downloaded videos - Alternating LLaVA/LLaMA models

SCRIPT_DIR="/mnt/Wolf-code/Wolf-Ai-Enterptises/writers/analysis"
DIT_DIR="/mnt/Wolf-code/Wolf-Ai-Enterptises/camera/dit"
LOG_FILE="/tmp/process_existing_videos_$(date +%Y%m%d_%H%M%S).log"

LLAVA_SCRIPT="$SCRIPT_DIR/youtube_analyst_llava.py"
LLAMA_SCRIPT="$SCRIPT_DIR/youtube_analyst_llama.py"

source ~/anaconda3/bin/activate messiah

echo "=============================================" | tee -a "$LOG_FILE"
echo "Processing Existing Videos - ALTERNATING MODELS" | tee -a "$LOG_FILE"
echo "Started: $(date)" | tee -a "$LOG_FILE"
echo "=============================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Find all video.mp4 files in DIT
video_num=0
for video_dir in $DIT_DIR/yt_*/; do
    video_file="$video_dir/video.mp4"

    if [ ! -f "$video_file" ]; then
        continue
    fi

    video_num=$((video_num + 1))

    # Alternate models
    if [ $((video_num % 2)) -eq 1 ]; then
        ANALYST_SCRIPT="$LLAVA_SCRIPT"
        MODEL_NAME="LLaVA 13b"
    else
        ANALYST_SCRIPT="$LLAMA_SCRIPT"
        MODEL_NAME="LLaMA 3.2 Vision 11b"
    fi

    echo "[$video_num] Processing: $video_file" | tee -a "$LOG_FILE"
    echo "Model: $MODEL_NAME" | tee -a "$LOG_FILE"
    echo "Size: $(du -h $video_file | cut -f1)" | tee -a "$LOG_FILE"
    echo "Started at: $(date)" | tee -a "$LOG_FILE"

    # Create temp URL file for analyst (it needs a URL)
    # Using video path directly - analyst will skip download if video exists
    python "$ANALYST_SCRIPT" "file://$video_file" --store --interval 15 2>&1 | tee -a "$LOG_FILE"

    exit_code=$?

    if [ $exit_code -eq 0 ]; then
        echo "✓ Complete: $(basename $video_dir) ($MODEL_NAME)" | tee -a "$LOG_FILE"
    else
        echo "✗ Failed: $(basename $video_dir) ($MODEL_NAME, exit code: $exit_code)" | tee -a "$LOG_FILE"
    fi

    echo "Finished at: $(date)" | tee -a "$LOG_FILE"
    echo "--------------------------------------------" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
done

echo "=============================================" | tee -a "$LOG_FILE"
echo "Processing complete - $video_num videos" | tee -a "$LOG_FILE"
echo "Ended: $(date)" | tee -a "$LOG_FILE"
echo "Log: $LOG_FILE" | tee -a "$LOG_FILE"
echo "=============================================" | tee -a "$LOG_FILE"
