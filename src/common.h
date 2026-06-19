#pragma once

#define MAX_CPUS 256
#define TASK_COMM_LEN 16

struct task_ctx {
    __u32 pid;
    char comm[TASK_COMM_LEN];
    __u64 vruntime;
    __u64 start_time;
    __u32 priority;
    bool is_ml_workload;
};

struct sched_stat {
    __u64 total_runtime_ns;
    __u64 context_switches;
    __u64 migrations;
    __u64 ml_tasks_scheduled;
};
