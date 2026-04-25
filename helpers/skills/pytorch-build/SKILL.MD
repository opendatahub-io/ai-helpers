---
description: PyTorch source build automation and debugging
globs:
  - pytorch/setup.py
  - pytorch/CMakeLists.txt
  - pytorch/build/**
  - scripts/build_pytorch.sh
alwaysApply: false
---

# PyTorch Build Automation

## Environment

| Property | Value |
|----------|-------|
| Workspace | `/path/to/your-container` |
| PyTorch source | `/workspaces/pytorch-devcontainers/pytorch` |
| Python | 3.13.9 |
| Virtual env | `/root/.venv` |
| CUDA | 12.8 at `/usr/local/cuda-12.8` |
| OS | Fedora 41 (Container) |

---

## Workflows

### When user says "build pytorch" or "build":

```bash
cd /workspaces/pytorch-devcontainers/pytorch
BUILD_TEST=0 MAX_JOBS=$(nproc) pip install -e .
python -c "import torch; print(f'✓ PyTorch {torch.__version__} | CUDA: {torch.cuda.is_available()}')"
```

### When user says "clean build" or "rebuild from scratch":

```bash
source /root/.venv/bin/activate
cd /workspaces/pytorch-devcontainers/pytorch
rm -rf build/
python setup.py clean
git submodule sync
git submodule update --init --recursive --force
BUILD_TEST=0 MAX_JOBS=$(nproc) pip install -e .
python -c "import torch; print(f'✓ PyTorch {torch.__version__} | CUDA: {torch.cuda.is_available()}')"
```

### When user says "debug build":

```bash
source /root/.venv/bin/activate
cd /workspaces/pytorch-devcontainers/pytorch
DEBUG=1 BUILD_TEST=0 MAX_JOBS=$(nproc) pip install -e .
python -c "import torch; print(f'✓ PyTorch {torch.__version__} (DEBUG) | CUDA: {torch.cuda.is_available()}')"
```

### When user says "setup.py develop" or "develop mode":

```bash
source /root/.venv/bin/activate
cd /workspaces/pytorch-devcontainers/pytorch
python setup.py develop
```

### When user says "verify torch" or "check install":

```bash
python -c "import torch; print(f'PyTorch {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}'); print(f'CUDA version: {torch.version.cuda if torch.cuda.is_available() else \"N/A\"}')"
```

---

## Build Environment Variables

Set these BEFORE running build commands:

| Variable | Purpose | Example |
|----------|---------|---------|
| `MAX_JOBS` | Parallel compile jobs | `export MAX_JOBS=$(nproc)` |
| `BUILD_TEST` | Build C++ tests (0=skip, faster) | `export BUILD_TEST=0` |
| `DEBUG` | Debug build with symbols | `export DEBUG=1` |
| `USE_CUDA` | Force CUDA build | `export USE_CUDA=1` |
| `USE_CUDNN` | Enable cuDNN | `export USE_CUDNN=1` |
| `USE_DISTRIBUTED` | Enable distributed training | `export USE_DISTRIBUTED=1` |
| `USE_MKLDNN` | Enable oneDNN/MKL-DNN | `export USE_MKLDNN=1` |

---

## Common Build Errors & Fixes

### `ninja: build stopped: subcommand failed`

**Cause:** C++ compilation error  
**Fix:**
1. Scroll up in terminal to find the actual error
2. Check `pytorch/build/CMakeFiles/CMakeError.log`
3. Fix the C++ issue and rebuild

### `undefined symbol` or `ImportError` after build

**Cause:** ABI mismatch or stale build artifacts  
**Fix:** Clean rebuild:
```bash
cd /workspaces/pytorch-devcontainers/pytorch
rm -rf build/
python setup.py clean
pip install -e .
```

### Out of memory during compilation

**Cause:** Too many parallel jobs  
**Fix:** Reduce parallelism:
```bash
MAX_JOBS=4 pip install -e .
```

### Submodule errors / missing dependencies

**Fix:**
```bash
cd /workspaces/pytorch-devcontainers/pytorch
git submodule sync
git submodule update --init --recursive --force
```

### `CUDA_HOME is not set`

**Fix:**
```bash
export CUDA_HOME=/usr/local/cuda
```

### `nvcc not found`

**Fix:**
```bash
export PATH=/usr/local/cuda-12.8/bin:$PATH
```

---

## Build Logs

When debugging build failures, check these files:

| Log | Location |
|-----|----------|
| CMake errors | `pytorch/build/CMakeFiles/CMakeError.log` |
| CMake output | `pytorch/build/CMakeFiles/CMakeOutput.log` |
| Compile commands | `pytorch/compile_commands.json` |

---
