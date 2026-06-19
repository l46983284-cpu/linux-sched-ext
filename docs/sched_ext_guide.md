# sched_ext guide

## What is sched_ext?

`sched_ext` is a Linux kernel feature, upstream in Linux 6.12+, that allows CPU schedulers to be implemented as BPF programs. This enables rapid iteration on scheduling policies without rebuilding the kernel for every experiment.

## Building

```bash
# Requires: clang, bpftool, libbpf, and kernel headers with sched_ext support
make
```

Portable checks that do not require a sched_ext kernel:

```bash
make check
```

Host capability preflight:

```bash
python3 tools/check_sched_ext.py --strict
```

## Usage

Use a dedicated development machine or VM. Do not attach experimental schedulers on production hosts.

```bash
# Load the scheduler (requires root + sched_ext enabled kernel)
sudo ./scx_userland ./scx_simple.bpf.o

# Check kernel support
cat /proc/sys/kernel/sched_ext/enable  # should be 1
```

## ML workload detection

The prototype currently detects ML-like workloads by process-name prefix:

- `python` (PyTorch, TensorFlow, data workers)
- `torch` (training processes)
- `jax` (JAX/Flax workloads)

ML workloads get longer time slices for throughput experiments. This is a scheduling hint, not a security boundary.

Generate synthetic workload pressure:

```bash
python3 examples/ml_burst.py --workers 4 --seconds 20
python3 examples/io_latency_probe.py --samples 100
```

## Benchmarking

Portable fork/exec latency smoke test:

```bash
python3 tools/benchmark.py --samples 100 --warmup 10 --json
```

For before/after scheduler comparison:

```bash
python3 tools/benchmark.py --samples 1000 --warmup 50 --json > baseline.json
sudo ./scx_userland ./scx_simple.bpf.o
python3 tools/benchmark.py --samples 1000 --warmup 50 --json > scx-simple.json
```

See [`testing.md`](testing.md) for the full validation workflow.

## Customization

Edit `src/scx_simple.bpf.c` to modify:

- `is_ml_process()`: workload detection heuristics.
- Time slice multipliers.
- Dispatch priority ordering.
- Runtime/stat counters.

Keep changes small and verifier-friendly. Update [`security_model.md`](security_model.md) when changing assumptions around isolation, privilege, or attach behavior.

## References

- [sched_ext kernel docs](https://docs.kernel.org/scheduler/sched-ext.html)
- [libbpf-bootstrap](https://github.com/libbpf/libbpf-bootstrap)
- [scx scheduler collection](https://github.com/sched-ext/scx)
