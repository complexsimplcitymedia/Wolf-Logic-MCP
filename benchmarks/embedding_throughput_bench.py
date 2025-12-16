#!/usr/bin/env python3
"""
Embedding Throughput Benchmark
Tests embedding generation speed across different models
Can run from any environment - uses Ollama HTTP API
"""

import requests
import time
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

OLLAMA_URL = "http://localhost:11434"

# Sample texts of varying lengths
SAMPLE_TEXTS = {
    "short": "The quick brown fox jumps over the lazy dog.",
    "medium": """Machine learning is a subset of artificial intelligence that enables
    systems to learn and improve from experience without being explicitly programmed.
    It focuses on developing algorithms that can access data and use it to learn for themselves.""",
    "long": """Artificial intelligence has transformed numerous industries in recent years,
    from healthcare to finance, transportation to entertainment. Machine learning models
    can now diagnose diseases, predict market trends, drive autonomous vehicles, and
    generate creative content. The field continues to evolve rapidly, with new architectures
    and training techniques emerging regularly. Large language models have demonstrated
    remarkable capabilities in understanding and generating human-like text, while
    computer vision systems can identify objects and patterns with superhuman accuracy.
    The implications of these advances are profound, raising important questions about
    the future of work, privacy, and the nature of intelligence itself."""
}

def get_embedding_models():
    """Get list of embedding models"""
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags")
        resp.raise_for_status()
        models = [m['name'] for m in resp.json().get('models', [])]
        # Filter to embedding models
        embed_keywords = ['embed', 'nomic', 'bge', 'mxbai', 'jina', 'snowflake', 'e5']
        return [m for m in models if any(k in m.lower() for k in embed_keywords)]
    except Exception as e:
        print(f"Error fetching models: {e}")
        return []

def generate_embedding(model, text):
    """Generate embedding for text"""
    payload = {
        "model": model,
        "input": text
    }

    start = time.perf_counter()
    try:
        resp = requests.post(f"{OLLAMA_URL}/api/embed", json=payload, timeout=60)
        resp.raise_for_status()
        elapsed = time.perf_counter() - start
        data = resp.json()
        embedding = data.get('embeddings', [[]])[0]
        return elapsed, len(embedding)
    except Exception as e:
        return None, 0

def benchmark_throughput(model, text, num_requests=50):
    """Benchmark embedding throughput with sequential requests"""
    times = []
    dims = 0

    for _ in range(num_requests):
        elapsed, dim = generate_embedding(model, text)
        if elapsed:
            times.append(elapsed)
            dims = dim

    if times:
        avg_time = sum(times) / len(times)
        throughput = len(times) / sum(times)
        return avg_time, throughput, dims
    return None, None, 0

def benchmark_concurrent(model, text, num_requests=50, workers=4):
    """Benchmark with concurrent requests"""
    start = time.perf_counter()
    completed = 0

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(generate_embedding, model, text) for _ in range(num_requests)]
        for future in as_completed(futures):
            elapsed, _ = future.result()
            if elapsed:
                completed += 1

    total_time = time.perf_counter() - start
    if completed > 0:
        return completed / total_time
    return 0

def unload_model(model):
    """Unload model to free VRAM"""
    try:
        requests.post(f"{OLLAMA_URL}/api/embed", json={
            "model": model,
            "input": "",
            "keep_alive": 0
        }, timeout=10)
    except:
        pass

def main():
    print("=" * 70)
    print("EMBEDDING THROUGHPUT BENCHMARK")
    print("=" * 70)

    # Check Ollama
    try:
        requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
    except:
        print("ERROR: Ollama not running at localhost:11434")
        sys.exit(1)

    models = get_embedding_models()
    if not models:
        print("No embedding models found!")
        print("Available models may not include embedding-specific models.")
        sys.exit(1)

    print(f"Found {len(models)} embedding models")
    print()

    results = []

    for model in models:
        print(f"\n{model}:")
        print(f"  {'Text':<8} | {'Dims':>6} | {'Avg (ms)':>10} | {'Seq/s':>8} | {'Conc/s':>8}")
        print(f"  {'-'*55}")

        model_throughputs = []

        for text_name, text in SAMPLE_TEXTS.items():
            avg_time, seq_throughput, dims = benchmark_throughput(model, text, num_requests=30)
            conc_throughput = benchmark_concurrent(model, text, num_requests=30, workers=4)

            if avg_time:
                print(f"  {text_name:<8} | {dims:>6} | {avg_time*1000:>10.2f} | {seq_throughput:>8.1f} | {conc_throughput:>8.1f}")
                model_throughputs.append(conc_throughput)
            else:
                print(f"  {text_name:<8} | {'---':>6} | {'error':>10} | {'---':>8} | {'---':>8}")

        if model_throughputs:
            results.append((model, sum(model_throughputs) / len(model_throughputs)))

        unload_model(model)
        time.sleep(0.5)

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY - Average Concurrent Throughput (embeddings/sec):")
    print("-" * 70)
    for model, avg_tp in sorted(results, key=lambda x: x[1], reverse=True):
        print(f"  {model:<50} {avg_tp:>8.1f}/s")

    print("\n" + "=" * 70)
    print("NOTE: Throughput varies by model size, text length, and hardware.")
    print("Concurrent throughput shows benefit of parallel requests.")
    print("=" * 70)

if __name__ == "__main__":
    main()
