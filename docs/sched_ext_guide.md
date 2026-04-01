# sched_ext Guide

## What is sched_ext?

sched_ext is a Linux kernel feature (merged in 6.12) that allows implementing CPU schedulers as BPF programs. This enables rapid iteration on scheduling policies without kernel recompilation.

## Building

```bash
# Requires: clang, bpftool, kernel headers with sched_ext support
make
```

## Usage

```bash
# Load the scheduler (requires root + sched_ext enabled kernel)
sudo ./scx_userland

# Check kernel support
cat /proc/sys/kernel/sched_ext/enable  # should be 1
```

## ML Workload Detection

The scheduler detects ML workloads by process name:
- `python` (PyTorch, TensorFlow)
- `torch` (training processes)
- `jax` (JAX/Flax)

ML workloads get 4x time slices for better GPU utilization.

## Customization

Edit `scx_simple.bpf.c` to modify:
- `is_ml_process()`: workload detection heuristics
- Time slice multipliers
- Dispatch priority ordering

## References
- [sched_ext kernel docs](https://docs.kernel.org/scheduler/sched-ext.html)
- [libbpf-bootstrap](https://github.com/libbpf/libbpf-bootstrap)
- [scx scheduler collection](https://github.com/sched-ext/scx)
