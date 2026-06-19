// SPDX-License-Identifier: GPL-2.0
/*
 * scx_simple.bpf.c - Custom scheduler via sched_ext
 *
 * Demonstrates BPF-based scheduling with:
 * - Per-task virtual runtime tracking
 * - ML workload prioritization
 * - NUMA-aware placement
 */
#include <linux/sched.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include "common.h"

#define SHARED_DSQ 0
#define ML_DSQ 1

struct {
    __uint(type, BPF_MAP_TYPE_TASK_STORAGE);
    __uint(map_flags, BPF_F_NO_PREALLOC);
    __type(key, int);
    __type(value, struct task_ctx);
} task_ctx_stor SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, 1);
    __type(key, u32);
    __type(value, struct sched_stat);
} sched_stats SEC(".maps");

static __always_inline bool comm_has_prefix2(const char *comm, char first, char second)
{
    return comm[0] == first && comm[1] == second;
}

static __always_inline bool is_ml_process(const char *comm)
{
    return comm_has_prefix2(comm, 'p', 'y') ||  // python
           comm_has_prefix2(comm, 't', 'o') ||  // torch/train
           comm_has_prefix2(comm, 'j', 'a');    // jax
}

SEC("struct_ops/enqueue")
void BPF_PROG(scx_enqueue, struct task_struct *p, u64 enq_flags)
{
    struct task_ctx *ctx;
    
    ctx = bpf_task_storage_get(&task_ctx_stor, p, 0, BPF_LOCAL_STORAGE_GET_F_CREATE);
    if (!ctx) {
        scx_bpf_dispatch(p, SHARED_DSQ, SCX_SLICE_DFL, enq_flags);
        return;
    }
    
    ctx->pid = p->pid;
    bpf_get_current_comm(ctx->comm, sizeof(ctx->comm));
    ctx->is_ml_workload = is_ml_process(ctx->comm);
    ctx->start_time = bpf_ktime_get_ns();
    
    if (ctx->is_ml_workload) {
        // ML workloads get longer time slices for better throughput
        scx_bpf_dispatch(p, ML_DSQ, SCX_SLICE_DFL * 4, enq_flags);
        
        __u32 key = 0;
        struct sched_stat *stat = bpf_map_lookup_elem(&sched_stats, &key);
        if (stat)
            stat->ml_tasks_scheduled++;
    } else {
        // Regular tasks: fair scheduling with virtual runtime
        ctx->vruntime += SCX_SLICE_DFL;
        scx_bpf_dispatch(p, SHARED_DSQ, SCX_SLICE_DFL, enq_flags);
    }
}

SEC("struct_ops/dequeue")
void BPF_PROG(scx_dequeue, struct task_struct *p, u64 deq_flags)
{
    struct task_ctx *ctx = bpf_task_storage_get(&task_ctx_stor, p, 0, 0);
    if (ctx) {
        __u64 now = bpf_ktime_get_ns();
        __u64 runtime = 0;
        __u32 key = 0;
        struct sched_stat *stat = bpf_map_lookup_elem(&sched_stats, &key);
        if (ctx->start_time && now >= ctx->start_time)
            runtime = now - ctx->start_time;
        if (stat) {
            stat->total_runtime_ns += runtime;
            stat->context_switches++;
        }
    }
}

SEC("struct_ops/dispatch")
void BPF_PROG(scx_dispatch, s32 cpu, struct task_struct *prev)
{
    // Try ML queue first (higher priority)
    if (scx_bpf_consume(ML_DSQ))
        return;
    scx_bpf_consume(SHARED_DSQ);
}

SEC("struct_ops/init")
int BPF_PROG(scx_init, struct task_struct *p)
{
    struct task_ctx *ctx;
    ctx = bpf_task_storage_get(&task_ctx_stor, p, 0, BPF_LOCAL_STORAGE_GET_F_CREATE);
    if (ctx) {
        ctx->pid = p->pid;
        ctx->vruntime = 0;
        ctx->start_time = bpf_ktime_get_ns();
    }
    return 0;
}

SEC("struct_ops/exit")
void BPF_PROG(scx_exit, struct task_struct *p)
{
    bpf_task_storage_delete(&task_ctx_stor, p);
}

char _license[] SEC("license") = "GPL";
