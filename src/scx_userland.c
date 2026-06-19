/*
 * scx_userland.c - User-space controller for the BPF scheduler
 *
 * Loads the BPF program, attaches to sched_ext, and prints runtime statistics.
 */
#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include <bpf/bpf.h>
#include <bpf/libbpf.h>

#include "common.h"

static volatile sig_atomic_t exiting = 0;

static void sig_handler(int sig)
{
    (void)sig;
    exiting = 1;
}

static int install_signal_handlers(void)
{
    struct sigaction sa;

    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = sig_handler;
    sigemptyset(&sa.sa_mask);

    if (sigaction(SIGINT, &sa, NULL) < 0)
        return -errno;
    if (sigaction(SIGTERM, &sa, NULL) < 0)
        return -errno;
    return 0;
}

static void print_stats(int map_fd)
{
    __u32 key = 0;
    struct sched_stat stat;

    memset(&stat, 0, sizeof(stat));
    if (bpf_map_lookup_elem(map_fd, &key, &stat) == 0) {
        printf("── Scheduler Stats ──────────────────────\n");
        printf("Total runtime:      %llu ns\n", stat.total_runtime_ns);
        printf("Context switches:   %llu\n", stat.context_switches);
        printf("Migrations:         %llu\n", stat.migrations);
        printf("ML tasks scheduled: %llu\n", stat.ml_tasks_scheduled);
        printf("─────────────────────────────────────────\n");
    } else {
        fprintf(stderr, "warning: failed to read sched_stats map: %s\n", strerror(errno));
    }
}

static void usage(const char *argv0)
{
    fprintf(stderr, "usage: %s [scx_simple.bpf.o]\n", argv0);
}

int main(int argc, char **argv)
{
    const char *obj_path = "scx_simple.bpf.o";
    struct bpf_object *obj = NULL;
    struct bpf_program *prog = NULL;
    struct bpf_link *link = NULL;
    int stats_fd = -1;
    int err = 0;

    if (argc > 2) {
        usage(argv[0]);
        return 2;
    }
    if (argc == 2)
        obj_path = argv[1];

    err = install_signal_handlers();
    if (err) {
        fprintf(stderr, "failed to install signal handlers: %s\n", strerror(-err));
        return 1;
    }

    printf("Loading sched_ext BPF scheduler: %s\n", obj_path);

    obj = bpf_object__open(obj_path);
    err = libbpf_get_error(obj);
    if (err) {
        fprintf(stderr, "failed to open BPF object '%s': %s\n", obj_path, strerror(-err));
        obj = NULL;
        goto cleanup;
    }

    err = bpf_object__load(obj);
    if (err) {
        fprintf(stderr, "failed to load BPF object: %s\n", strerror(-err));
        goto cleanup;
    }

    prog = bpf_object__find_program_by_name(obj, "scx_init");
    if (!prog) {
        fprintf(stderr, "failed to find BPF program 'scx_init'\n");
        err = -ENOENT;
        goto cleanup;
    }

    link = bpf_program__attach(prog);
    err = libbpf_get_error(link);
    if (err) {
        fprintf(stderr, "failed to attach BPF program: %s\n", strerror(-err));
        link = NULL;
        goto cleanup;
    }

    stats_fd = bpf_object__find_map_fd_by_name(obj, "sched_stats");
    if (stats_fd < 0)
        fprintf(stderr, "warning: sched_stats map not found; running without stats\n");

    printf("Scheduler attached. Press Ctrl+C to stop.\n\n");
    while (!exiting) {
        if (stats_fd >= 0)
            print_stats(stats_fd);
        sleep(2);
    }

cleanup:
    if (link)
        bpf_link__destroy(link);
    if (obj)
        bpf_object__close(obj);

    if (err) {
        fprintf(stderr, "scheduler exited with error: %s\n", strerror(-err));
        return 1;
    }

    printf("\nScheduler detached.\n");
    return 0;
}
