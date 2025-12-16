#!/bin/bash
# Test incept5/llama3.1-claude by having it run the baseline check
# Compare its results with Claude's reference baseline

echo "=========================================="
echo "INCEPT5 JOB APPLICATION TEST"
echo "=========================================="
echo ""
echo "Task: Run the same baseline check Claude just ran"
echo "Expected: Results should match Claude's baseline"
echo ""

# Activate messiah environment
source ~/anaconda3/bin/activate messiah

# Have incept5 run the baseline check script
echo "Running baseline check via incept5/llama3.1-claude..."
echo ""

ollama run incept5/llama3.1-claude:latest <<'PROMPT'
You are being tested for a system monitoring job.

Your task:
1. Run this Python script: /mnt/Wolf-code/Wolf-Ai-Enterptises/security/baseline_check.py
2. Report the baseline hash you get
3. Compare your results to the reference baseline at: /mnt/Wolf-code/Wolf-Ai-Enterptises/security/baselines/baseline_20251206_085042.json

Expected reference hash: 8876a8e2f6c402f23a807a855410876cdf59e395f3949a3717dec5a73b245105

Execute the baseline check now.
PROMPT

echo ""
echo "=========================================="
echo "COMPARISON TEST COMPLETE"
echo "=========================================="
