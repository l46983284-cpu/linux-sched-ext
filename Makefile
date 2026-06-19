KDIR ?= /lib/modules/$(shell uname -r)/build
CLANG ?= clang
BPFTOOL ?= bpftool
PYTHON ?= python3
CC ?= cc
CFLAGS ?= -O2 -Wall -Wextra
LIBBPF_CFLAGS ?= $(shell pkg-config --cflags libbpf 2>/dev/null)
LIBBPF_LIBS ?= $(shell pkg-config --libs libbpf 2>/dev/null || echo -lbpf -lelf -lz)

.PHONY: all clean check test benchmark-smoke preflight build-optional

all: scx_simple.bpf.o scx_userland

scx_simple.bpf.o: src/scx_simple.bpf.c src/common.h
	$(CLANG) -O2 -target bpf -g -c $< -o $@

scx_userland: src/scx_userland.c src/common.h
	$(CC) $(CFLAGS) $(LIBBPF_CFLAGS) -o $@ $< $(LIBBPF_LIBS)

check: test benchmark-smoke preflight

test:
	$(PYTHON) -m unittest discover -s tests -v

benchmark-smoke:
	$(PYTHON) tools/benchmark.py --samples 5 --warmup 1 --json

preflight:
	$(PYTHON) tools/check_sched_ext.py

build-optional:
	$(MAKE) all || { \
		echo "optional scheduler build skipped/failed; sched_ext kernel headers may be unavailable"; \
		exit 0; \
	}

clean:
	rm -f scx_simple.bpf.o scx_userland
