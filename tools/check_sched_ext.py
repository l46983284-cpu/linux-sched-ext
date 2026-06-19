#!/usr/bin/env python3
"""Preflight checks for linux-sched-ext experiments.

This script is intentionally read-only. It reports whether the current host has
the tools and kernel surfaces commonly needed for sched_ext/BPF scheduler work.
"""
from __future__ import annotations

import argparse
import os
import pathlib
import platform
import shutil
import subprocess
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Check:
    name: str
    ok: bool
    detail: str


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def kernel_release() -> str:
    return platform.release()


def kernel_version_tuple(release: str) -> tuple[int, int]:
    head = release.split("-", 1)[0]
    parts = head.split(".")
    try:
        return int(parts[0]), int(parts[1])
    except (IndexError, ValueError):
        return 0, 0


def file_exists(path: str) -> bool:
    return pathlib.Path(path).exists()


def run_text(command: list[str]) -> str:
    try:
        return subprocess.check_output(command, text=True, stderr=subprocess.STDOUT, timeout=3).strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def collect_checks() -> list[Check]:
    release = kernel_release()
    major, minor = kernel_version_tuple(release)
    checks = [
        Check("kernel-version", (major, minor) >= (6, 12), f"running {release}; sched_ext is upstream in Linux 6.12+"),
        Check("clang", command_exists("clang"), shutil.which("clang") or "missing"),
        Check("bpftool", command_exists("bpftool"), shutil.which("bpftool") or "missing"),
        Check("llvm-objdump", command_exists("llvm-objdump"), shutil.which("llvm-objdump") or "missing"),
        Check("kernel-headers", file_exists(f"/lib/modules/{release}/build"), f"/lib/modules/{release}/build"),
        Check("sched-ext-sysctl", file_exists("/proc/sys/kernel/sched_ext/enable"), "/proc/sys/kernel/sched_ext/enable"),
        Check("root-or-sudo", os.geteuid() == 0 or command_exists("sudo"), "attach requires root privileges"),
    ]

    if command_exists("bpftool"):
        feature = run_text(["bpftool", "feature", "probe", "kernel", "unprivileged"])
        checks.append(Check("bpftool-probe", bool(feature), "bpftool can probe kernel features" if feature else "probe failed"))
    return checks


def render(checks: Iterable[Check]) -> str:
    lines = []
    for check in checks:
        mark = "OK" if check.ok else "WARN"
        lines.append(f"[{mark:4}] {check.name:18} {check.detail}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="return non-zero when any check warns")
    args = parser.parse_args()

    checks = collect_checks()
    print(render(checks))
    if args.strict and not all(check.ok for check in checks):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
