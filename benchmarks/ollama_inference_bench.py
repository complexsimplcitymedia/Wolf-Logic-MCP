#!/usr/bin/env python3
"""
Ollama Inference Benchmark
Tests token generation speed across different models
Can run from any environment - uses Ollama HTTP API
"""

import requests
import time
import json
import sys

OLLAMA_URL = "http://localhost:11434"

def get_available_models():
    """Get list of available models"""
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags")
        resp.raise_for_status()
        return [m['name'] for m in resp.json().get('models', [])]
    except Exception as e:
        print(f"Error fetching models: {e}")
        return []

def benchmark_generation(model, prompt, max_tokens=100):
    """Benchmark token generation for a model"""
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,
        "options": {
            "num_predict": max_tokens,
            "temperature": 0.7
        }
    }

    tokens = 0
    first_token_time = None
    start_time = time.perf_counter()

    try:
        with requests.post(f"{OLLAMA_URL}/api/generate", json=payload, stream=True, timeout=120) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if line:
                    data = json.loads(line)
                    if 'response' in data and data['response']:
                        tokens += 1
                        if first_token_time is None:
                            first_token_time = time.perf_counter() - start_time
                    if data.get('done', False):
                        break
    except requests.exceptions.Timeout:
        return None, None, None
    except Exception as e:
        print(f"  Error: {e}")
        return None, None, None

    total_time = time.perf_counter() - start_time

    if tokens > 0 and first_token_time:
        tokens_per_sec = tokens / (total_time - first_token_time) if total_time > first_token_time else 0
        return first_token_time, tokens_per_sec, tokens
    return None, None, None

def unload_model(model):
    """Unload a model to free VRAM"""
    try:
        requests.post(f"{OLLAMA_URL}/api/generate", json={
            "model": model,
            "prompt": "",
            "keep_alive": 0
        }, timeout=10)
    except:
        pass

def main():
    print("=" * 70)
    print("OLLAMA INFERENCE BENCHMARK")
    print("=" * 70)

    # Check Ollama is running
    try:
        requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
    except:
        print("ERROR: Ollama not running at localhost:11434")
        sys.exit(1)

    models = get_available_models()
    if not models:
        print("No models found!")
        sys.exit(1)

    print(f"Found {len(models)} models")
    print()

    # Test prompts
    prompts = [
        ("Short", "What is 2+2?"),
        ("Medium", "Explain the concept of recursion in programming in a few sentences."),
        ("Long", "Write a detailed explanation of how neural networks learn, including backpropagation and gradient descent.")
    ]

    # Filter to LLM models (skip embedding models)
    llm_models = [m for m in models if not any(x in m.lower() for x in ['embed', 'nomic', 'bge', 'mxbai', 'jina', 'snowflake', 'e5'])]

    print(f"Testing {len(llm_models)} LLM models:")
    print("-" * 70)

    results = []

    for model in llm_models:
        print(f"\n{model}:")
        print(f"  {'Prompt':<8} | {'TTFT (s)':>10} | {'Tokens/s':>10} | {'Tokens':>8}")
        print(f"  {'-'*50}")

        model_results = []
        for prompt_name, prompt in prompts:
            ttft, tps, tokens = benchmark_generation(model, prompt, max_tokens=100)
            if ttft is not None:
                print(f"  {prompt_name:<8} | {ttft:>10.3f} | {tps:>10.1f} | {tokens:>8}")
                model_results.append((prompt_name, ttft, tps, tokens))
            else:
                print(f"  {prompt_name:<8} | {'timeout':>10} | {'---':>10} | {'---':>8}")

        if model_results:
            avg_tps = sum(r[2] for r in model_results) / len(model_results)
            results.append((model, avg_tps))

        # Unload to free VRAM for next model
        unload_model(model)
        time.sleep(1)

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY - Average Tokens/Second:")
    print("-" * 70)
    for model, avg_tps in sorted(results, key=lambda x: x[1], reverse=True):
        print(f"  {model:<45} {avg_tps:>10.1f} tok/s")

    print("\n" + "=" * 70)
    print("REFERENCE (7B models on various GPUs):")
    print("  RTX 4090: ~140-160 tok/s")
    print("  RTX 4080: ~100-120 tok/s")
    print("  RX 7900 XTX: ~90-110 tok/s")
    print("  RX 7900 XT: ~80-100 tok/s")
    print("=" * 70)

if __name__ == "__main__":
    main()
