MATCH
(parent_wakeup_new:sched_wakeup_new)

WITH parent_wakeup_new
MATCH (child_exit:sched_process_exit)
WHERE child_exit.common_pid = parent_wakeup_new.pid

WITH parent_wakeup_new, child_exit
MATCH
(child_exit)-[:per_pid*1..]->(child_wakeup:sched_wakeup)

WITH parent_wakeup_new, child_exit, child_wakeup
MATCH
(parent_block)-[:block]->(child_wakeup)-[:unblock]->(parent_unblock)

WITH parent_wakeup_new, child_exit, child_wakeup, parent_block, parent_unblock
MATCH
(parent_wait:sched_process_wait)-[:per_switch*]->()-[:per_cpu]->(parent_block)

RETURN parent_wakeup_new, child_exit, child_wakeup, parent_block, parent_unblock, parent_wait;
