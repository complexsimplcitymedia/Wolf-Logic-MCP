#!/usr/bin/env python3
"""
GPU Compute Benchmark - Matrix Multiplication / GEMM
Run in ROCm environment: conda activate rocm
"""

import torch
import time
import sys

def benchmark_matmul(size, dtype=torch.float32, iterations=100, warmup=10):
    """Benchmark matrix multiplication"""
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # Create random matrices
    a = torch.randn(size, size, dtype=dtype, device=device)
    b = torch.randn(size, size, dtype=dtype, device=device)

    # Warmup
    for _ in range(warmup):
        c = torch.matmul(a, b)
    torch.cuda.synchronize()

    # Benchmark
    start = time.perf_counter()
    for _ in range(iterations):
        c = torch.matmul(a, b)
    torch.cuda.synchronize()
    elapsed = time.perf_counter() - start

    # Calculate TFLOPS (2 * N^3 operations for matmul)
    flops = 2 * (size ** 3) * iterations
    tflops = flops / elapsed / 1e12

    return elapsed / iterations, tflops

def main():
    print("=" * 60)
    print("GPU COMPUTE BENCHMARK - Matrix Multiplication")
    print("=" * 60)

    if not torch.cuda.is_available():
        print("ERROR: CUDA/ROCm not available!")
        print("Make sure you're in the ROCm environment: conda activate rocm")
        sys.exit(1)

    print(f"Device: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    print()

    sizes = [1024, 2048, 4096, 8192, 16384]
    dtypes = [
        (torch.float32, "FP32"),
        (torch.float16, "FP16"),
    ]

    # Check for bfloat16 support
    if hasattr(torch.cuda, 'is_bf16_supported') and torch.cuda.is_bf16_supported():
        dtypes.append((torch.bfloat16, "BF16"))

    for dtype, dtype_name in dtypes:
        print(f"\n{'=' * 60}")
        print(f"Precision: {dtype_name}")
        print(f"{'=' * 60}")
        print(f"{'Size':>8} | {'Time (ms)':>12} | {'TFLOPS':>10}")
        print("-" * 40)

        for size in sizes:
            try:
                # Adjust iterations for larger sizes
                iters = max(10, 100 // (size // 1024))
                avg_time, tflops = benchmark_matmul(size, dtype=dtype, iterations=iters)
                print(f"{size:>8} | {avg_time*1000:>12.3f} | {tflops:>10.2f}")
            except RuntimeError as e:
                if "out of memory" in str(e).lower():
                    print(f"{size:>8} | {'OOM':>12} | {'---':>10}")
                    torch.cuda.empty_cache()
                else:
                    raise

    print("\n" + "=" * 60)
    print("REFERENCE (approximate):")
    print("  RTX 4090: ~80-83 TFLOPS FP32, ~165 TFLOPS FP16")
    print("  RTX 4080: ~49 TFLOPS FP32, ~97 TFLOPS FP16")
    print("  RX 7900 XTX: ~61 TFLOPS FP32, ~123 TFLOPS FP16")
    print("  RX 7900 XT: ~51 TFLOPS FP32, ~103 TFLOPS FP16")
    print("=" * 60)

if __name__ == "__main__":
    main()
