# Monthly Cost Comparison — ECS Fargate



## 1. Purpose and status



This document compares two illustrative ECS Fargate configurations for the Reliable Pipeline Service in AWS `ap-south-1` (Asia Pacific — Mumbai).



**Status:** Planning estimate only. The application currently runs locally with a mocked downstream dependency. No AWS deployment or production bill has been verified.



All figures are in USD, before taxes, credits, and applicable discounts. Prices can change; verify them with the AWS Pricing Calculator before deployment.



## 2. Traffic assumptions



The assignment's traffic profile is:



| Period (UTC) | Target traffic |

|---|---:|

| 00:00–08:00 | 10 calls/min |

| 08:00–10:00 | Ramp from 10 to 50 calls/min, then hold |

| 10:00–14:00 | 10 calls/min |

| 14:00–16:00 | Ramp from 10 to 50 calls/min, then hold |

| 16:00–24:00 | 10 calls/min |



The model assumes 20 baseline hours and 4 campaign hours per day. To illustrate a monthly cost, it assumes 30 days of operation.



These estimates use illustrative task counts, not measured application throughput. The actual number of tasks required must be determined by load testing, including request concurrency, retry overhead, and latency objectives.



## 3. Configurations



| Parameter | Configuration A: larger tasks | Configuration B: smaller tasks |

|---|---|---|

| CPU per task | 1 vCPU | 0.5 vCPU |

| Memory per task | 2 GB | 1 GB |

| Minimum tasks | 1 | 1 |

| Maximum tasks | 5 | 10 |

| Assumed baseline tasks | 1 | 1 |

| Assumed average campaign tasks | 4 | 7 |

| Purpose | More capacity per task | Finer scaling increments |



Both configurations retain at least one task for service availability behind the Application Load Balancer. The assumed campaign task counts are illustrative and must be validated against the custom scaling metric and measured capacity.



## 4. Fargate compute estimate



For this planning calculation, the approximate Mumbai Linux/x86 rates are:



- vCPU: $0.04256 per vCPU-hour

- Memory: $0.004655 per GB-hour



These rates are reference inputs, not a price guarantee. Confirm the current regional rates before deployment.



### Configuration A



Estimated task-hour consumption per day:



- Baseline: 20 hours × 1 task = 20 task-hours

- Campaign: 4 hours × 4 tasks = 16 task-hours

- Total: 36 task-hours/day



Monthly task-hours = 36 × 30 = 1,080.



Estimated cost per task-hour:



(1 × $0.04256) + (2 × $0.004655) = $0.05187.



Estimated monthly compute:



1,080 × $0.05187 = **$56.02**.



### Configuration B



Estimated task-hour consumption per day:



- Baseline: 20 hours × 1 task = 20 task-hours

- Campaign: 4 hours × 7 tasks = 28 task-hours

- Total: 48 task-hours/day



Monthly task-hours = 48 × 30 = 1,440.



Estimated cost per task-hour:



(0.5 × $0.04256) + (1 × $0.004655) = $0.025935.



Estimated monthly compute:



1,440 × $0.025935 = **$37.35**.



The smaller-task configuration has a lower estimated compute cost under these assumed task counts. This does not prove it will meet the same latency or throughput objectives; benchmarking is required.



## 5. Shared infrastructure estimate



The following shared charges are illustrative and apply to either configuration.



| Component | Monthly planning estimate | Assumption |

|---|---:|---|

| Application Load Balancer | $23.29 | Approximately 730 hours at $0.0239/hour plus an assumed average of 1 LCU at $0.008/LCU-hour |

| NAT Gateway | $40.88 | One gateway for 730 hours at an indicative $0.056/hour |

| NAT data processing | $5.60 | Assumes 100 GB processed at an indicative $0.056/GB |

| **Shared infrastructure total** | **$69.77** | Before other networking and logging charges |



ALB charges depend on the highest applicable Load Balancer Capacity Unit dimension, including connections, bytes processed, and rule evaluations. NAT Gateway costs include both provisioned hours and data processing. Actual usage may differ.



## 6. Monthly comparison



| Cost category | Configuration A | Configuration B |

|---|---:|---:|

| Fargate compute | $56.02 | $37.35 |

| Application Load Balancer | $23.29 | $23.29 |

| NAT Gateway hours | $40.88 | $40.88 |

| NAT data processing | $5.60 | $5.60 |

| **Estimated monthly total** | **$125.79** | **$107.12** |



Under the stated assumptions, Configuration B is approximately $18.67/month less expensive. This comparison is illustrative, not a measured result.



## 7. Exclusions and limitations



The estimates do not include:



- CloudWatch log ingestion, retention, custom metrics, dashboards, or alarms.

- ECR image storage and image transfer.

- Additional data transfer, cross-AZ traffic, or NAT processing beyond the assumed 100 GB.

- Additional NAT Gateways for availability across multiple Availability Zones.

- TLS certificates, Route 53, domain registration, or other optional services.

- GPU-based STT, LLM, or TTS inference.

- Taxes, credits, Savings Plans, or Spot discounts.



The current application uses a mocked dependency and does not incur GPU inference charges locally. These estimates do not include the cost of hosting actual open-weight models.



## 8. Validation plan



Before treating either estimate as a deployment budget:



1. Enter the intended task CPU, memory, and scaling parameters into the AWS Pricing Calculator for `ap-south-1`.

2. Confirm ALB capacity usage and NAT data-processing assumptions.

3. Load-test baseline and campaign traffic while measuring p50, p90, p99, concurrent requests, retries, and queue depth.

4. Verify that autoscaling uses an appropriate in-flight-request or queue-depth metric rather than CPU alone.

5. Compare actual resource consumption with the estimate and update the table.

6. Tear down temporary resources after the demonstration and verify that chargeable resources have been removed.



## 9. References



- AWS Fargate pricing: https://aws.amazon.com/fargate/pricing/

- AWS Elastic Load Balancing pricing: https://aws.amazon.com/elasticloadbalancing/pricing/

- AWS VPC and NAT Gateway pricing: https://aws.amazon.com/vpc/pricing/



All prices and totals in this document are estimates, not evidence of an actual AWS deployment or bill.
