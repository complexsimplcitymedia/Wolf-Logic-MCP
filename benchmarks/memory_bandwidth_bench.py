#!/usr/bin/env python3
"""
GPU Memory Bandwidth Benchmark
Run in ROCm environment: conda activate rocm
"""

import torch
import time
import sys

def benchmark_memory_bandwidth(size_gb=1.0, iterations=100, warmup=10):
    """Benchmark GPU memory bandwidth with copy operations"""
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # Calculate number of float32 elements for target size
    num_elements = int(size_gb * 1e9 / 4)  # 4 bytes per float32

    # Create tensors
    src = torch.randn(num_elements, dtype=torch.float32, device=device)
    dst = torch.empty_like(src)

    # Warmup
    for _ in range(warmup):
        dst.copy_(src)
    torch.cuda.synchronize()

    # Benchmark
    start = time.perf_counter()
    for _ in range(iterations):
        dst.copy_(src)
    torch.cuda.synchronize()
    elapsed = time.perf_counter() - start

    # Calculate bandwidth (read + write = 2x data moved)
    bytes_moved = 2 * num_elements * 4 * iterations
    bandwidth_gbps = bytes_moved / elapsed / 1e9

    return elapsed / iterations, bandwidth_gbps

def benchmark_h2d_d2h(size_gb=1.0, iterations=50):
    """Benchmark Host-to-Device and Device-to-Host transfers"""
    device = torch.device('cuda')
    num_elements = int(size_gb * 1e9 / 4)

    # Host tensor (pinned memory for faster transfers)
    host_tensor = torch.randn(num_elements, dtype=torch.float32).pin_memory()
    device_tensor = torch.empty(num_elements, dtype=torch.float32, device=device)

    # Warmup
    for _ in range(5):
        device_tensor.copy_(host_tensor)
        host_tensor.copy_(device_tensor.cpu())
    torch.cuda.synchronize()

    # H2D benchmark
    start = time.perf_counter()
    for _ in range(iterations):
        device_tensor.copy_(host_tensor)
    torch.cuda.synchronize()
    h2d_time = time.perf_counter() - start
    h2d_bandwidth = (num_elements * 4 * iterations) / h2d_time / 1e9

    # D2H benchmark
    host_dst = torch.empty_like(host_tensor).pin_memory()
    start = time.perf_counter()
    for _ in range(iterations):
        host_dst.copy_(device_tensor)
    torch.cuda.synchronize()
    d2h_time = time.perf_counter() - start
    d2h_bandwidth = (num_elements * 4 * iterations) / d2h_time / 1e9

    return h2d_bandwidth, d2h_bandwidth

def main():
    print("=" * 60)
    print("GPU MEMORY BANDWIDTH BENCHMARK")
    print("=" * 60)

    if not torch.cuda.is_available():
        print("ERROR: CUDA/ROCm not available!")
        print("Make sure you're in the ROCm environment: conda activate rocm")
        sys.exit(1)

    props = torch.cuda.get_device_properties(0)
    print(f"Device: {props.name}")
    print(f"VRAM: {props.total_memory / 1e9:.1f} GB")
    print()

    # Device-to-Device bandwidth
    print("Device-to-Device Memory Bandwidth:")
    print("-" * 40)
    print(f"{'Size (GB)':>10} | {'Time (ms)':>12} | {'BW (GB/s)':>12}")
    print("-" * 40)

    for size in [0.5, 1.0, 2.0, 4.0]:
        try:
            avg_time, bandwidth = benchmark_memory_bandwidth(size_gb=size)
            print(f"{size:>10.1f} | {avg_time*1000:>12.3f} | {bandwidth:>12.1f}")
        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                print(f"{size:>10.1f} | {'OOM':>12} | {'---':>12}")
                torch.cuda.empty_cache()
            else:
                raise

    # PCIe bandwidth (Host <-> Device)
    print("\nPCIe Transfer Bandwidth:")
    print("-" * 40)
    try:
        h2d, d2h = benchmark_h2d_d2h(size_gb=1.0)
        print(f"Host-to-Device: {h2d:.1f} GB/s")
        print(f"Device-to-Host: {d2h:.1f} GB/s")
    except Exception as e:
        print(f"Error: {e}")

    print("\n" + "=" * 60)
    print("REFERENCE (theoretical peak):")
    print("  RTX 4090: 1008 GB/s GDDR6X")
    print("  RTX 4080: 717 GB/s GDDR6X")
    print("  RX 7900 XTX: 960 GB/s GDDR6")
    print("  RX 7900 XT: 800 GB/s GDDR6")
    print("  PCIe 4.0 x16: ~25-28 GB/s (practical)")
    print("=" * 60)

if __name__ == "__main__":
    main()
