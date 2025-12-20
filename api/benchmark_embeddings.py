#!/usr/bin/env python3
"""
Embedding Model Benchmark - CPU vs GPU
Test qwen3-embedding:4b performance on 14700K vs RX 7900 XT
"""

import time
import ollama
import statistics
import os
from datetime import datetime

# Test texts of varying lengths
TEST_TEXTS = [
    "Short test",
    "This is a medium length sentence that represents a typical memory entry in the database system.",
    "This is a much longer text that simulates a complex memory entry with multiple sentences and detailed information about a specific topic. It contains various technical details, contextual information, and metadata that would typically be stored in the wolf_logic database for semantic search and retrieval operations.",
    " ".join(["word"] * 100),  # 100 words
    " ".join(["word"] * 500),  # 500 words
]

BATCH_SIZES = [1, 10, 50, 100]
MODEL = "qwen3-embedding:4b"

def generate_embedding(text: str, num_gpu: int = None):
    """Generate embedding with optional GPU specification"""
    options = {}
    if num_gpu is not None:
        options['num_gpu'] = num_gpu

    start = time.time()
    response = ollama.embeddings(model=MODEL, prompt=text, options=options)
    latency = time.time() - start

    return response['embedding'], latency

def benchmark_single(device: str, num_gpu: int = None):
    """Benchmark single embedding generation"""
    print(f"\n{'='*60}")
    print(f"SINGLE EMBEDDING - {device}")
    print(f"{'='*60}")

    results = []

    for i, text in enumerate(TEST_TEXTS):
        latencies = []

        # Warmup
        generate_embedding(text, num_gpu)

        # Run 10 iterations
        for _ in range(10):
            _, latency = generate_embedding(text, num_gpu)
            latencies.append(latency)

        avg_latency = statistics.mean(latencies)
        std_dev = statistics.stdev(latencies) if len(latencies) > 1 else 0

        print(f"Text {i+1} ({len(text)} chars):")
        print(f"  Avg: {avg_latency*1000:.2f}ms")
        print(f"  Std: {std_dev*1000:.2f}ms")
        print(f"  Min: {min(latencies)*1000:.2f}ms")
        print(f"  Max: {max(latencies)*1000:.2f}ms")

        results.append({
            'text_length': len(text),
            'avg_latency_ms': avg_latency * 1000,
            'std_dev_ms': std_dev * 1000
        })

    return results

def benchmark_batch(device: str, num_gpu: int = None):
    """Benchmark batch embedding generation"""
    print(f"\n{'='*60}")
    print(f"BATCH EMBEDDING - {device}")
    print(f"{'='*60}")

    results = []

    for batch_size in BATCH_SIZES:
        batch_text = TEST_TEXTS[1]  # Use medium-length text
        latencies = []

        # Warmup
        for _ in range(batch_size):
            generate_embedding(batch_text, num_gpu)

        # Run 5 iterations
        for _ in range(5):
            start = time.time()
            for _ in range(batch_size):
                generate_embedding(batch_text, num_gpu)
            latency = time.time() - start
            latencies.append(latency)

        avg_latency = statistics.mean(latencies)
        throughput = batch_size / avg_latency

        print(f"Batch size: {batch_size}")
        print(f"  Total time: {avg_latency*1000:.2f}ms")
        print(f"  Per item: {(avg_latency/batch_size)*1000:.2f}ms")
        print(f"  Throughput: {throughput:.2f} embeddings/sec")

        results.append({
            'batch_size': batch_size,
            'total_time_ms': avg_latency * 1000,
            'per_item_ms': (avg_latency / batch_size) * 1000,
            'throughput': throughput
        })

    return results

def run_benchmark():
    """Run full benchmark suite"""
    print(f"\n{'#'*60}")
    print(f"# EMBEDDING BENCHMARK - {MODEL}")
    print(f"# Date: {datetime.now().isoformat()}")
    print(f"# CPU: Intel 14700K")
    print(f"# GPU: AMD RX 7900 XT")
    print(f"{'#'*60}")

    # CPU Benchmark (num_gpu=0 forces CPU)
    print("\n\n*** CPU BENCHMARK ***")
    cpu_single = benchmark_single("CPU (14700K)", num_gpu=0)
    cpu_batch = benchmark_batch("CPU (14700K)", num_gpu=0)

    # GPU Benchmark (num_gpu=1 uses GPU)
    print("\n\n*** GPU BENCHMARK ***")
    gpu_single = benchmark_single("GPU (RX 7900 XT)", num_gpu=1)
    gpu_batch = benchmark_batch("GPU (RX 7900 XT)", num_gpu=1)

    # Summary comparison
    print(f"\n\n{'='*60}")
    print("SUMMARY - CPU vs GPU")
    print(f"{'='*60}")

    # Average across all single tests
    cpu_avg = statistics.mean([r['avg_latency_ms'] for r in cpu_single])
    gpu_avg = statistics.mean([r['avg_latency_ms'] for r in gpu_single])

    print(f"\nSingle Embedding (average across all text lengths):")
    print(f"  CPU: {cpu_avg:.2f}ms")
    print(f"  GPU: {gpu_avg:.2f}ms")
    print(f"  Speedup: {cpu_avg/gpu_avg:.2f}x" if gpu_avg < cpu_avg else f"  GPU slower by: {gpu_avg/cpu_avg:.2f}x")

    # Batch throughput comparison (batch_size=100)
    cpu_throughput = next(r['throughput'] for r in cpu_batch if r['batch_size'] == 100)
    gpu_throughput = next(r['throughput'] for r in gpu_batch if r['batch_size'] == 100)

    print(f"\nBatch Throughput (100 embeddings):")
    print(f"  CPU: {cpu_throughput:.2f} embeddings/sec")
    print(f"  GPU: {gpu_throughput:.2f} embeddings/sec")
    print(f"  Speedup: {gpu_throughput/cpu_throughput:.2f}x" if gpu_throughput > cpu_throughput else f"  GPU slower by: {cpu_throughput/gpu_throughput:.2f}x")

    # Recommendation
    print(f"\n{'='*60}")
    print("RECOMMENDATION")
    print(f"{'='*60}")

    if cpu_throughput >= gpu_throughput * 0.8:  # If CPU is within 80% of GPU
        print(f"\n✓ USE CPU for embeddings")
        print(f"  - CPU performance is {cpu_throughput/gpu_throughput*100:.1f}% of GPU")
        print(f"  - Save GPU VRAM (21.4GB) for LLM inference")
        print(f"  - 14700K has {os.cpu_count()} cores - plenty of headroom")
    else:
        print(f"\n✓ USE GPU for embeddings")
        print(f"  - GPU is {gpu_throughput/cpu_throughput:.2f}x faster")
        print(f"  - Worth the VRAM allocation")
        print(f"  - CPU can focus on API serving")

    print(f"\n{'='*60}\n")

if __name__ == "__main__":
    run_benchmark()
