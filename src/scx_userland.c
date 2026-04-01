/*
 * scx_userland.c - User-space controller for the BPF scheduler
 *
 * Loads the BPF program, attaches to sched_ext, and provides
 * runtime statistics.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>
#include <errno.h>
#include <bpf/libbpf.h>
#include <bpf/bpf.h>
#include "common.h"

static volatile int exiting = 0;

static void sig_handler(int sig)
{
    exiting = 1;
}

static void print_stats(int map_fd)
{
    u32 key = 0;
    struct sched_stat stat;
    
    if (bpf_map_lookup_elem(map_fd, &key, &stat) == 0) {
        printf("── Scheduler Stats ──────────────────────\n");
        printf("Total runtime:      %llu ns\n", stat.total_runtime_ns);
        printf("Context switches:   %llu\n", stat.context_switches);
        printf("Migrations:         %llu\n", stat.migrations);
        printf("ML tasks scheduled: %llu\n", stat.ml_tasks_scheduled);
        printf("─────────────────────────────────────────\n");
    }
}

int main(int argc, char **argv)
{
    struct bpf_object *obj;
    struct bpf_link *link;
    int err;
    
    signal(SIGINT, sig_handler);
    signal(SIGTERM, sig_handler);
    
    printf("Loading scx_simple BPF scheduler...\n");
    
    obj = bpf_object__open("scx_simple.bpf.o");
    if (libbpf_get_error(obj)) {
        fprintf(stderr, "Failed to open BPF object\n");
        return 1;
    }
    
    err = bpf_object__load(obj);
    if (err) {
        fprintf(stderr, "Failed to load BPF object: %d\n", err);
        return 1;
    }
    
    struct bpf_program *prog = bpf_object__find_program_by_name(obj, "scx_init");
    if (!prog) {
        fprintf(stderr, "Failed to find BPF program\n");
        return 1;
    }
    
    link = bpf_program__attach(prog);
    if (libbpf_get_error(link)) {
        fprintf(stderr, "Failed to attach BPF program\n");
        return 1;
    }
    
    printf("Scheduler attached. Press Ctrl+C to stop.\n\n");
    
    int stats_fd = bpf_object__find_map_fd_by_name(obj, "sched_stats");
    
    while (!exiting) {
        if (stats_fd >= 0)
            print_stats(stats_fd);
        sleep(2);
    }
    
    printf("\nDetaching scheduler...\n");
    bpf_link__destroy(link);
    bpf_object__close(obj);
    return 0;
}
