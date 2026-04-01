#pragma once

#define MAX_CPUS 256
#define TASK_COMM_LEN 16

struct task_ctx {
    u32 pid;
    char comm[TASK_COMM_LEN];
    u64 vruntime;
    u64 start_time;
    u32 priority;
    bool is_ml_workload;
};

struct sched_stat {
    u64 total_runtime_ns;
    u64 context_switches;
    u64 migrations;
    u64 ml_tasks_scheduled;
};
