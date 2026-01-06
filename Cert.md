Hi,

We’ve analyzed the Spark job failure and the root cause is clear.

The job fails during an HTTPS call to your API endpoint with an SSL error:
**certificate verify failed – self-signed certificate / missing CA in the trust chain**.

In our Spark-as-a-Service solution, the Spark base image is supposed to embed all **known BNP internal CAs**.
At this stage, it appears that **the certificate (or its issuing CA) used by the API you are calling is not present in the Spark image truststore**, which explains why the call works in other environments but fails when executed from Spark pods (driver/executors).

### Suggested remediation options

* **Preferred (clean solution)**
  Add the missing root/intermediate CA to the Spark runtime trust:

  * either by updating the Spark base image
  * or by injecting the certificate via ConfigMap/Secret and referencing it at runtime

* **Alternative workaround**
  Inject the certificate directly into the **JRE cacerts** used by Spark (driver and executors), so both JVM and Python HTTPS clients trust the endpoint.

* **Temporary workaround (non-prod only)**
  Disable SSL verification at application level (e.g. `verify=False` in requests) — not recommended for production.

From our side, the Spark platform and code execution are behaving as expected; the issue is strictly related to **certificate trust configuration**.

Let us know which option you’d like to proceed with, and we can assist accordingly.

Best regards,
Djamel
