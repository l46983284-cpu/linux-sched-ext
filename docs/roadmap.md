# Roadmap

This roadmap tracks the work needed to turn `linux-sched-ext` from a small prototype into a reproducible scheduler lab.

## v0.1.0 — portable validation

- [x] Public repository layout with source, docs, examples, and CI.
- [x] Portable benchmark tool with machine-readable JSON output.
- [x] Unit tests for benchmark parsing and statistics.
- [x] Security model and review checklist.
- [ ] Release notes and first tagged release.

## v0.2.0 — sched_ext integration hardening

- [ ] Validate build on a known sched_ext-enabled kernel.
- [ ] Add loader diagnostics for missing libbpf, bpftool, and kernel config.
- [ ] Record scheduler attach/detach behavior in a test matrix.
- [ ] Add failure-mode docs for verifier rejection and unsupported kernels.

## v0.3.0 — workload policy experiments

- [ ] Replace process-prefix detection with configurable workload rules.
- [ ] Add mixed CPU/GPU pressure benchmarks.
- [ ] Track starvation/fairness metrics per workload class.
- [ ] Add cgroup-aware policy hooks where sched_ext support allows it.

## v0.4.0 — review automation

- [ ] Codex-assisted review prompts for C/eBPF scheduler diffs.
- [ ] CI checks for docs, examples, and benchmark regressions.
- [ ] Release workflow with signed artifacts where appropriate.
- [ ] Issue templates for scheduler bugs and benchmark reports.
