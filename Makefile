KDIR ?= /lib/modules/$(shell uname -r)/build
CLANG ?= clang
BPFTOOL ?= bpftool

.PHONY: all clean

all: scx_simple.bpf.o scx_userland

scx_simple.bpf.o: src/scx_simple.bpf.c src/common.h
	$(CLANG) -O2 -target bpf -g -c $< -o $@

scx_userland: src/scx_userland.c src/common.h
	$(CC) -O2 -Wall -o $@ $<

clean:
	rm -f scx_simple.bpf.o scx_userland
