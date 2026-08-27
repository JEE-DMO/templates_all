Hello Team,

From our investigation on the Airflow/Astronomer side, we can see that the affected tasks successfully establish the Oracle connection and start the MERGE/stored procedure execution. However, for the impacted runs, the call remains waiting for several hours without any further activity on the Airflow side.

We also observed that some runs complete normally while others remain stuck, with the degradation starting around **August 6th**.

As we do not have access to the Oracle environment, could you please perform a deeper investigation on the database side, especially while a task is stuck:

* Check Oracle session wait events (`EVENT`, `WAIT_CLASS`, `SECONDS_IN_WAIT`).
* Check for blocking sessions, locks or row/table contention.
* Identify the SQL_ID and execution status of the MERGE/stored procedure.
* Check for long-running/orphan sessions or uncommitted transactions from previous runs.
* Review AWR/ASH around the affected periods and compare with the situation before August 6th.
* Check whether any database change, execution plan change or performance degradation occurred around August 6th.

At this stage, the Airflow task appears to be waiting for the Oracle call to return, so identifying **what the Oracle session is waiting for during an impacted run** would be the key point for the investigation.

Regards,
Djamel
