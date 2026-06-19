# Testing and validation

`linux-sched-ext` separates portable validation from kernel-dependent scheduler experiments.

## Portable checks

These checks should pass on ordinary CI runners and developer laptops:

```bash
make check
```

This runs:

1. Python unit tests for benchmark/statistics code.
2. A short benchmark smoke test with JSON output.
3. A read-only sched_ext host preflight.

The preflight can print `WARN` entries on machines without Linux 6.12+, `clang`, or `/proc/sys/kernel/sched_ext/enable`; warnings do not fail portable checks because most CI runners cannot attach sched_ext schedulers.

## Optional scheduler build

On a development host with the BPF toolchain installed:

```bash
make build-optional
```

This attempts to compile both the BPF object and user-space loader. The target is intentionally non-fatal in CI because public runners may lack sched_ext headers even when clang/libbpf are available.

## Manual scheduler experiment

Use a dedicated development machine or VM. Do not attach experimental schedulers on production hosts.

```bash
python3 tools/check_sched_ext.py --strict
make
sudo ./scx_userland ./scx_simple.bpf.o
```

In a second terminal, generate workload pressure:

```bash
python3 examples/ml_burst.py --workers 4 --seconds 20
python3 examples/io_latency_probe.py --samples 100 --sleep 0.001
```

Capture before/after benchmark data:

```bash
python3 tools/benchmark.py --samples 1000 --warmup 50 --json > baseline.json
# attach scheduler
python3 tools/benchmark.py --samples 1000 --warmup 50 --json > scx-simple.json
```

## Reporting results

Open a benchmark report issue with:

- Kernel release and distro.
- CPU model and core count.
- `tools/check_sched_ext.py` output.
- Exact benchmark commands.
- Raw JSON results.
