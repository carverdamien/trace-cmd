When a task is scheduled, it was previously either blocked or ready. compute_sched_switch_latency() compute these latencies and stores them in the sched_switch dataframe.
When `latency_type` is `W` (wakeup latency), `latency_value` measures the time between the `sched_switch` and the `sched_wakeup` that wakes up this task.
When `latency_type` is `P` (preempt latency), `latency_value` measure the time between the `sched_switch` and the last `sched_switch` of this task.
