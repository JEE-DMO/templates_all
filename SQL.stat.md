SELECT
    date_trunc('hour', created) AS hour,
    user,
    count(*) AS nb_running_queries,
    max(elapsed_time) AS max_elapsed_time,
    max(cpu_time) AS max_cpu_time,
    max(queued_time) AS max_queued_time
FROM system.runtime.queries
WHERE created >= current_timestamp - interval '15' day
GROUP BY 1, 2
ORDER BY hour DESC, max_elapsed_time DESC;
