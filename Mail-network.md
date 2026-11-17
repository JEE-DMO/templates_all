Subject: Long-running DB sessions dropped after ~10 min - network check requested

Hi team,

We are seeing long-running database sessions being dropped from one of our Airflow workloads connecting to an Oracle database. The connections appear to be closed after roughly 10 minutes of inactivity, even though the database itself shows no error on its side.

Example occurrence (UTC):
- Start: 2026-11-13, 15:15:16
- Failure: 2026-11-13, 15:26:35
- Symptom: connection reset / broken pipe on the client side while waiting for the database response

Could you please help us understand whether something on the network path could be closing idle connections? In particular, it would be great if you could:

1. Check whether any device on the path between the Kubernetes cluster and the Oracle database (firewall, NAT, load balancer, proxy) applies an idle/session timeout on this flow.
2. Let us know the configured value, and whether it is possible to adjust it for this flow or handle keepalive traffic differently.
3. Check the logs around the timestamps above for any session teardown related to this flow.

Happy to share more details (source/destination and flow information) through the appropriate channel if needed.

Thanks in advance for your help.

Best regards
