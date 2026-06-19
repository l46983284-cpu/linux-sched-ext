# Security model

`linux-sched-ext` is an experimental scheduler prototype. It is designed for development machines and kernel labs, not production hosts.

## Assets and boundaries

The important boundary is the Linux scheduler path. A faulty policy can affect:

- CPU fairness and starvation behavior.
- Latency-sensitive system daemons.
- Workload isolation between interactive and batch tasks.
- Kernel stability when BPF verifier constraints are violated.
- Reliability of CI/release automation that builds or packages scheduler artifacts.

## Threats considered

### Policy-level mistakes

A scheduler can be memory-safe and still harmful if it starves tasks, over-prioritizes a workload class, or produces pathological dispatch ordering.

Mitigations:

- Keep dispatch queues explicit and limited.
- Track runtime counters for policy decisions.
- Add benchmarks for mixed latency/throughput workloads before changing defaults.
- Gate production-facing claims until real sched_ext kernels are tested.

### Kernel-facing C/eBPF defects

BPF verifier checks reduce risk but do not replace code review. The project avoids dynamic memory, unbounded loops, and ambiguous pointer lifetime patterns.

Review checklist:

- Map accesses checked for null returns.
- Fixed-size string handling only.
- Explicit bounds on CPU/task counters.
- Clear cleanup path for task-local storage.
- No hidden dependency on process names for security decisions.

### Privilege and operational risk

Attaching a scheduler requires elevated privileges. Running experiments on a shared or production host can interrupt unrelated workloads.

Mitigations:

- `tools/check_sched_ext.py` warns about missing kernel support/dependencies before attach.
- Documentation calls out dev-kernel-only status.
- CI runs portable tests without requiring privileged scheduler attach.

## Non-goals

- This project does not claim to provide production-grade workload isolation.
- Process-name workload classification is a scheduling hint, not an access-control mechanism.
- The current prototype does not enforce cgroup or tenant-level policy.

## Review focus for Codex Security

Codex Security review would be most useful for:

- C/eBPF verifier-sensitive patterns.
- Scheduler starvation and fairness edge cases.
- Unsafe user-space loader error paths.
- CI/release scripts that run privileged commands or package artifacts.
