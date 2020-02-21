PROFILE

MATCH
(woken:sched_switch)-[:block]->(waker:sched_wakeup)-[:unblock]->(:sched_switch)

RETURN
DISTINCT([woken.common_pid, waker.common_pid]), COUNT(*) as wakeup_count
ORDER BY wakeup_count DESC
LIMIT 30
;

PROFILE

MATCH
(woken:sched_switch)-[:block]->(waker:sched_wakeup)-[:unblock]->(:sched_switch)

RETURN
DISTINCT([woken.common_pid, woken.common_comm, waker.common_pid, waker.common_comm]), COUNT(*) as wakeup_count
ORDER BY wakeup_count DESC
LIMIT 30
;

PROFILE

MATCH
(woken:sched_switch)-[:block]->(waker:sched_wakeup)-[:unblock]->(:sched_switch)

RETURN
DISTINCT([woken.common_pid, woken.common_comm, waker.common_pid, waker.common_comm]) as woken_waker, COUNT(*) as wakeup_count
ORDER BY wakeup_count DESC
LIMIT 30
;

// CREATE INDEX FOR (exec:sched_process_exec) ON (exec.common_pid);
// CALL db.awaitIndexes;

PROFILE

MATCH
(woken:sched_switch)-[:block]->(waker:sched_wakeup)-[:unblock]->(:sched_switch)

WITH
DISTINCT([woken.common_pid, woken.common_comm, waker.common_pid, waker.common_comm]) as woken_waker, COUNT(*) as wakeup_count
OPTIONAL MATCH
(woken_exec:sched_process_exec)
WHERE
woken_exec.common_pid = woken_waker[0]

WITH woken_waker, woken_exec, wakeup_count
OPTIONAL MATCH
(waker_exec:sched_process_exec)
WHERE
waker_exec.common_pid = woken_waker[2]

RETURN

woken_waker[0] as woken_pid,

CASE
WHEN
woken_waker[1] = "<...>"
THEN
woken_exec.filename
ELSE
woken_waker[1]
END
as woken_comm,

woken_waker[2] as waker_pid,

CASE
WHEN
woken_waker[3] = "<...>"
THEN
waker_exec.filename
ELSE
woken_waker[3]
END
as waker_comm,

wakeup_count ORDER BY wakeup_count DESC
LIMIT 30
;
