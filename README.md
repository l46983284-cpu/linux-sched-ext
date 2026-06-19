# linux-sched-ext

`linux-sched-ext` is an experimental Linux `sched_ext`/BPF scheduler for ML and latency-sensitive workloads. The project focuses on reproducible scheduler experiments, workload classification, and safety-oriented review around kernel-facing scheduling code.

> Status: early-stage research prototype. The code is intended for development kernels with `sched_ext` support, not production hosts.

## Why this exists

`sched_ext` lets scheduler policy live in BPF instead of requiring a full kernel rebuild. That makes it practical to test workload-specific scheduling ideas while keeping the kernel boundary explicit and reviewable.

This repository explores:

- ML workload detection from process metadata.
- Separate dispatch queues for latency-sensitive and throughput-heavy tasks.
- Runtime accounting for scheduler decisions.
- Reproducible benchmarking for fork/exec and mixed workload latency.
- Security review practices for C/eBPF code that touches scheduling and isolation.

## Repository layout

```text
src/
  scx_simple.bpf.c    Minimal sched_ext BPF scheduler
  scx_userland.c      User-space loader and stats printer
  common.h            Shared BPF/user-space structs
config/
  workload_rules.example.json  Reviewable user-space workload classification rules
tools/
  benchmark.py                 Fork/exec latency benchmark with JSON output
  check_sched_ext.py           Host capability and dependency preflight
  classify_workload.py         Rule-based workload classification smoke tool
examples/
  ml_burst.py         Synthetic ML-like CPU workload generator
docs/
  sched_ext_guide.md  Build/run notes
  security_model.md   Threat model and safety checklist
  roadmap.md          Project roadmap and milestones
tests/
  test_benchmark.py   Unit tests for benchmark tooling
```

## Requirements

Runtime scheduler experiments need:

- Linux kernel with `sched_ext` support enabled.
- `clang`, `llvm`, `bpftool`, kernel headers.
- `libbpf` development headers for the loader.
- Root privileges to attach a scheduler.

Tooling/tests can run on ordinary CI hosts without a sched_ext kernel.

## Quick start

Check local support:

```bash
python3 tools/check_sched_ext.py
```

Run tests and benchmark smoke checks:

```bash
make check
```

Try the reviewable workload classifier rules:

```bash
python3 tools/classify_workload.py python3 --json
```

Build on a supported host:

```bash
make
```

Attach the scheduler on a development machine:

```bash
sudo ./scx_userland ./scx_simple.bpf.o
```

Run a small benchmark:

```bash
python3 tools/benchmark.py --samples 100 --warmup 10 --json
```

Generate synthetic CPU pressure:

```bash
python3 examples/ml_burst.py --workers 4 --seconds 20
```

## Safety notes

Scheduler code runs close to one of the most sensitive kernel boundaries. This project treats correctness and reviewability as first-class goals:

- Keep BPF programs small and verifier-friendly.
- Prefer explicit runtime accounting over implicit policy.
- Test user-space tooling without requiring privileged kernel features.
- Document assumptions and known limitations before adding policy complexity.
- Never run experimental schedulers on production machines.

See [`docs/security_model.md`](docs/security_model.md) for the full checklist.

## Current limitations

- Workload classification is intentionally simple and based on process names.
- NUMA and GPU feedback loops are planned, not complete.
- The BPF scheduler is a prototype and needs validation on real sched_ext kernels.
- Benchmarks currently measure fork/exec latency as a portable proxy; more workload-specific traces are on the roadmap.

## License

GPL-2.0 for scheduler/kernel-facing code. See [`LICENSE`](LICENSE).
