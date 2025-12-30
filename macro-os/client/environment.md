# Miniconda3 Environment Configuration

## Why Miniconda3 (Not Anaconda3)

Miniconda3 is the minimal conda installer. It includes:
- conda package manager
- Python
- Essential dependencies

It does NOT include:
- 250+ pre-installed packages you don't need
- GUI tools (Anaconda Navigator)
- 3GB+ of disk space waste

For Wolf Logic clients, Miniconda3 is sufficient. You install only what you need.

## Installation Paths

| Platform | Recommended Path | Why |
|----------|------------------|-----|
| Linux | `~/miniconda3/` | Home directory, no sudo needed |
| macOS | `~/miniconda3/` | Home directory, no admin needed |
| Shared system | `/opt/miniconda3/` | System-wide, requires sudo |

## Environment: client-memory

This is your Wolf Logic client environment. It contains only what's needed to query the memory layer.

### Create Environment

```bash
# Create with Python 3.12
conda create -n client-memory python=3.12 -y

# Activate
conda activate client-memory

# Verify
python --version  # Python 3.12.x
which python      # ~/miniconda3/envs/client-memory/bin/python
```

### Required Packages

| Package | Source | Purpose |
|---------|--------|---------|
| psycopg2 | conda-forge | PostgreSQL adapter |
| ollama | pip | Ollama client (for submissions) |
| requests | pip | HTTP client (for MCP intake API) |
| pydantic | pip | Data validation |

### Install Packages

```bash
conda activate client-memory

# psycopg2 from conda-forge (binary, no compile needed)
conda install -c conda-forge psycopg2 -y

# Python packages from pip
pip install ollama requests pydantic
```

### Export Environment

Save your environment for replication:

```bash
# Export to YAML
conda env export > ~/wolf-logic-client/environment.yml

# Contents will look like:
cat ~/wolf-logic-client/environment.yml
```

Example `environment.yml`:
```yaml
name: client-memory
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.12
  - psycopg2
  - pip
  - pip:
    - ollama
    - requests
    - pydantic
```

### Recreate from YAML

On a new machine:

```bash
conda env create -f environment.yml
conda activate client-memory
```

## Shell Integration

### Auto-activate on Login

Add to `~/.bashrc` or `~/.zshrc`:

```bash
# Auto-activate client-memory environment
if [ -f ~/miniconda3/etc/profile.d/conda.sh ]; then
    source ~/miniconda3/etc/profile.d/conda.sh
    conda activate client-memory
fi
```

### Environment Variables

Create `~/.config/wolf-logic/env`:

```bash
# Wolf Logic Client Configuration

# Conda environment
export CONDA_DEFAULT_ENV="client-memory"

# Local PostgreSQL
export LOCAL_PG_HOST="localhost"
export LOCAL_PG_PORT="5432"
export LOCAL_PG_DB="wolf_logic_local"
export LOCAL_PG_USER="${USER}"

# Hub (181)
export HUB_PG_HOST="100.110.82.181"
export HUB_PG_PORT="5433"
export HUB_PG_DB="wolf_logic"
export HUB_PG_USER="wolf"
export HUB_PG_PASSWORD="wolflogic2024"

# MCP API
export MCP_INTAKE_URL="http://100.110.82.181:8002"
```

Load in shell:
```bash
echo 'source ~/.config/wolf-logic/env' >> ~/.bashrc
source ~/.bashrc
```

## Common Conda Commands

```bash
# List environments
conda env list

# Activate environment
conda activate client-memory

# Deactivate
conda deactivate

# Update all packages
conda update --all -y

# Remove environment (if needed)
conda env remove -n client-memory

# Clean cache (free disk space)
conda clean --all -y
```

## Troubleshooting

### "conda: command not found"

```bash
# Re-initialize conda
~/miniconda3/bin/conda init bash  # or zsh
source ~/.bashrc
```

### "psycopg2: libpq.so.5 not found"

This happens with pip-installed psycopg2. Use conda-forge version:

```bash
pip uninstall psycopg2 psycopg2-binary -y
conda install -c conda-forge psycopg2 -y
```

### "Environment already exists"

```bash
# Remove and recreate
conda env remove -n client-memory
conda create -n client-memory python=3.12 -y
```

### "Solving environment takes forever"

Use mamba (faster solver):

```bash
conda install -n base -c conda-forge mamba -y
mamba create -n client-memory python=3.12 -y
mamba install -c conda-forge psycopg2 -y
```

## Package Versions (Reference)

As of December 2025:

```
python          3.12.x
psycopg2        2.9.x
ollama          0.4.x
requests        2.31.x
pydantic        2.10.x
```

Pin versions if needed:

```bash
pip install ollama==0.4.0 requests==2.31.0 pydantic==2.10.0
```

## Comparison: Miniconda3 vs Anaconda3

| Feature | Miniconda3 | Anaconda3 |
|---------|------------|-----------|
| Download size | ~80MB | ~800MB |
| Installed size | ~400MB | ~3GB+ |
| Pre-installed packages | ~20 | 250+ |
| GUI tools | No | Yes |
| Sufficient for Wolf Logic | Yes | Overkill |
| Install time | 2 min | 15+ min |

**Conclusion:** Use Miniconda3. Install only what you need.
