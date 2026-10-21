\# Cost Analysis



\## Local Prototype



The prototype runs on an existing Windows computer using Python, FastAPI, and SQLite. Its downstream speech-processing dependency is mocked, so it does not require GPU hosting, model inference services, or other cloud infrastructure.



No incremental cloud-service charges were incurred for the local prototype. Electricity consumption and developer time were not separately measured, so no precise local operating cost is claimed.



\## Production Considerations



A production deployment could incur costs for API compute, GPU-based model inference, persistent storage, logging and monitoring, networking, load balancing, and data transfer. The actual cost would depend on traffic volume, concurrency, model size, latency targets, deployment region, and autoscaling configuration.



Before estimating production costs, the service should be benchmarked with representative traffic and the intended open-weight models. The estimate should account for idle capacity, retries, observability, and network charges. Always-on GPU hosting should be compared with autoscaled or managed inference options.



No AWS deployment or production cloud bill was measured as part of this local prototype. Therefore, this write-up describes the observed local setup and the cost factors that would need to be measured for a production deployment; it does not claim measured AWS costs.
