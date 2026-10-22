\# Reliable Pipeline Service — Runbook



\## 1. Purpose



This runbook explains how to set up, run, test, and troubleshoot the Reliable Pipeline Service.



The current application is a local prototype with simulated downstream processing. The AWS Terraform configuration is prepared for review, but a successful AWS deployment has not yet been verified.



\## 2. Prerequisites



\- Python 3.12 or a compatible Python version

\- Git

\- Terraform 1.5 or later for infrastructure validation

\- Docker for building and running the container image

\- AWS CLI and appropriately scoped AWS credentials for eventual deployment



Do not use AWS root credentials for routine infrastructure deployment. Configure an appropriately scoped IAM identity before deploying.



\## 3. Local Setup



Run commands from the repository root.



Activate the virtual environment in PowerShell:



```powershell

.\\.venv\\Scripts\\Activate.ps1

```



Install dependencies:



```powershell

python -m pip install -r requirements.txt

```



Start the API:



```powershell

python -m uvicorn main:app --host 127.0.0.1 --port 8000

```



Open a second PowerShell terminal to run the following checks.



Health check:



```powershell

Invoke-RestMethod http://127.0.0.1:8000/health

```



Metrics endpoint:



```powershell

Invoke-RestMethod http://127.0.0.1:8000/metrics

```



The metrics endpoint exposes process-local request counts, active requests, and observed latency percentiles. These values are not a substitute for verified CloudWatch metrics.



\## 4. Run Tests



Run the test suite:



```powershell

python -m pytest -q

```



A passing result indicates that the tests completed successfully in the local environment. It does not establish that the service works correctly in AWS.



\## 5. Pipeline API



The main processing endpoint is:



```http

POST /pipeline/process

Content-Type: application/json

```



Example request:



```json

{

&#x20; "event\_id": "demo-event-001",

&#x20; "audio\_ref": "synthetic"

}

```



PowerShell example:



```powershell

$body = @{

&#x20;   event\_id = "demo-event-001"

&#x20;   audio\_ref = "synthetic"

} | ConvertTo-Json



Invoke-RestMethod `

&#x20;   -Method Post `

&#x20;   -Uri http://127.0.0.1:8000/pipeline/process `

&#x20;   -ContentType "application/json" `

&#x20;   -Body $body

```



The service uses simulated downstream processing rather than a production speech-to-text, language-model, and text-to-speech stack.



Inspect the API implementation and README for the current request and response schemas and the available DLQ endpoints.



\## 6. Reliability Features



The application is designed to demonstrate:



\- Retry and backoff behaviour for transient downstream failures.

\- Circuit breaking to limit repeated calls to an unhealthy dependency.

\- Idempotency handling for repeated event submissions.

\- SQLite-backed persistence for local processing and dead-letter records.

\- Dead-letter inspection and replay.

\- HTTP health and application metrics endpoints.



These features should be tested with the provided test suite before changes are committed.



\## 7. Troubleshooting



\### API does not start



1\. Activate the virtual environment.

2\. Install dependencies from `requirements.txt`.

3\. Check the terminal for Python import errors.

4\. Confirm port 8000 is not already in use.



\### Tests fail



1\. Run the failing test individually.

2\. Read the assertion and traceback.

3\. Check whether the test depends on persistent local database state.

4\. Rerun the full test suite after the fix.



\### SQLite state causes unexpected results



Stop the application before investigating the local database. Do not delete the database if its records are needed for debugging or demonstration.



\### CloudWatch metrics are missing



The application publishes the custom `ConcurrentRequests` metric only when CloudWatch publishing is enabled and the required ECS environment variables are configured.



For AWS deployment, verify:



\- The task role has permission to publish the metric.

\- The container received the expected environment variables.

\- The task can reach the CloudWatch API.

\- The task logs contain no metric-publishing errors.

\- The metric appears in the `ReliablePipeline` namespace.



Metric publication and alarm behaviour have not yet been verified in a deployed AWS environment.



\## 8. Terraform Validation



From the repository root, format the Terraform configuration:



```powershell

terraform -chdir=infra/terraform fmt

```



Validate the configuration:



```powershell

terraform -chdir=infra/terraform validate

```



Validation checks configuration consistency and syntax. It does not prove that AWS deployment will succeed.



Before any deployment:



1\. Review the Terraform plan.

2\. Confirm the target AWS account and region.

3\. Review IAM permissions and resource exposure.

4\. Estimate costs, including NAT Gateway, load balancer, compute, logs, and data transfer.

5\. Confirm service quotas and container-image availability.

6\. Obtain explicit approval before applying changes.



Do not run `terraform apply` without authorization and a cost review.



\## 9. Container Image



The Dockerfile is located at `docker/Dockerfile`.



After Docker is installed and working, build from the repository root:



```powershell

docker build -f docker/Dockerfile -t reliable-pipeline:local .

```



Run the image locally:



```powershell

docker run --rm -p 8000:8000 reliable-pipeline:local

```



Then check the health endpoint:



```powershell

Invoke-RestMethod http://127.0.0.1:8000/health

```



These commands are instructions only; a successful Docker build and container run have not yet been verified.



\## 10. Deployment Status



Current status:



\- Local API and reliability tests: implemented.

\- Terraform configuration: formatted and validated locally.

\- CloudWatch dashboard configuration: prepared.

\- Container image: not yet built or published.

\- AWS deployment: not verified.

\- Real open-weight model integration: not implemented.

\- AWS load test, failure-injection demonstration, and teardown evidence: pending.



Update this section only when each item has been verified with actual evidence.s
