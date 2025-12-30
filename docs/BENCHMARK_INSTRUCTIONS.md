# Infrastructure Benchmark Instructions

## What This Tests

The benchmark script compares **Workstation (100.110.82.181)** vs **Bookworm Cloud (100.110.82.250)** across:

1. **PostgreSQL Performance**
   - SELECT 1000 rows
   - COUNT all records
   - Complex JOIN queries
   - INSERT 10 records

2. **MySQL Performance**
   - INSERT 100 records
   - SELECT all records
   - UPDATE 50 records
   - DELETE all records

3. **Ollama Embedding Performance**
   - Single embedding generation (qwen3-embedding:4b)
   - Batch 10 embeddings

4. **Disk I/O Performance**
   - Write speed (1GB file)
   - Read speed (1GB file)

5. **Network Performance**
   - Ping latency between environments

## How to Run

```bash
# Activate messiah environment
source ~/anaconda3/bin/activate messiah

# Run benchmark
python /mnt/Wolf-code/Wolf-Ai-Enterptises/scripty/benchmark_infrastructure.py
```

## Expected Runtime

- Total benchmark time: ~5-10 minutes
- Each environment tested independently
- Results saved to `/mnt/Wolf-code/Wolf-Ai-Enterptises/docs/BENCHMARK_REPORT_[timestamp].md`

## Output Files

1. **BENCHMARK_REPORT_[timestamp].md** - Human-readable comparison report
2. **BENCHMARK_REPORT_[timestamp].json** - Raw benchmark data (JSON)

## What to Look For

### PostgreSQL
- **Lower times = better** (faster queries)
- Workstation has more RAM → may be faster for complex queries
- Cloud has newer SSDs → may be faster for I/O-bound operations

### MySQL
- **Lower times = better**
- Both environments have similar MySQL setups
- Should be relatively even

### Ollama
- **Lower times = better**
- Workstation has AMD RX 7900 XT GPU
- Cloud has no GPU (CPU only)
- **Workstation should dominate embedding benchmarks**

### Disk I/O
- **Higher MB/s = better** (faster disk)
- Workstation: 2x 1TB NVMe in RAID0 (1.8TB total)
- Cloud: 2x 954GB NVMe in RAID0 (933GB total)
- **Should be relatively close** (both NVMe)

### Network
- **Lower latency = better**
- Both on Tailscale mesh network
- Expected: <5ms latency (local network)

## Troubleshooting

### PostgreSQL connection failed
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Check port is accessible
nc -zv 100.110.82.181 5433
nc -zv 100.110.82.250 5432
```

### MySQL connection failed
```bash
# Check if MySQL is running
docker ps | grep mysql

# Check credentials
docker exec mysql-test mysql -uroot -pwolflogic2024 -e "SELECT 1;"
```

### Ollama connection failed
```bash
# Check if Ollama is running
curl http://100.110.82.181:11434/api/tags
curl http://100.110.82.250:11434/api/tags

# Check qwen3-embedding:4b is loaded
ollama list | grep qwen3-embedding
```

## Sample Output

```
================================================================================
INFRASTRUCTURE BENCHMARK REPORT
Workstation (100.110.82.181) vs Bookworm Cloud (100.110.82.250)
Generated: 2025-12-19 17:00:00
================================================================================

## POSTGRESQL PERFORMANCE

| Metric                  | Workstation      | Cloud            | Winner      |
|-------------------------|------------------|------------------|-------------|
| select_1000_rows        |         0.0234s |         0.0256s | Workstation (9.4% faster) |
| count_all               |         0.0012s |         0.0015s | Workstation (25.0% faster) |
| complex_join            |         0.0456s |         0.0489s | Workstation (7.2% faster) |
| insert_10_records       |         0.0123s |         0.0118s | Cloud (4.2% faster) |

## MYSQL PERFORMANCE
...
```

## Use Cases

1. **Migration Validation**: Verify cloud environment performs acceptably before moving production
2. **Performance Tuning**: Identify bottlenecks (CPU, disk, network)
3. **Capacity Planning**: Understand which workloads fit which environment
4. **Cost Optimization**: Workstation has GPU (expensive) - can cloud handle embeddings CPU-only?

## Next Steps After Benchmarking

1. **If Cloud is slower**: Optimize Docker configs, tune PostgreSQL/MySQL settings
2. **If Workstation is much faster**: Keep heavy workloads (Ollama embeddings) on workstation
3. **If results are close**: Safe to migrate everything to cloud
4. **If network latency is high**: Consider consolidating services on one environment
