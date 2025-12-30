#!/bin/bash
# Sync critical Ollama models from 181 to MacBook

echo "Pulling critical models from 181 manifest..."

# Primary Librarian
ollama pull qwen3-embedding:4b

# Extraction LLM
ollama pull qwen2.5:0.5b

# Key embedding models
ollama pull bge-large:latest
ollama pull mxbai-embed-large:latest
ollama pull snowflake-arctic-embed:137m
ollama pull jina/jina-embeddings-v2-base-en:latest
ollama pull jina/jina-embeddings-v2-base-de:latest
ollama pull unclemusclez/jina-embeddings-v2-base-code:latest
ollama pull jeffh/intfloat-multilingual-e5-large-instruct:q8_0
ollama pull dengcao/Qwen3-Embedding-0.6B:q8_0
ollama pull embeddinggemma:latest
ollama pull nomic-embed-text:v1.5

# Small LLMs for local inference
ollama pull llama3.2:1b

echo "✓ Critical models synced"
ollama list
