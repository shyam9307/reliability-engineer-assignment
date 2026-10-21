import random
import statistics


SAMPLES = 100_000

# Match the current mock dependency's latency calculation.
latencies_ms = [
    random.lognormvariate(5.7, 0.60)
    for _ in range(SAMPLES)
]

latencies_ms.sort()


def percentile(values, percentile_value):
    index = round((percentile_value / 100) * (len(values) - 1))
    return values[index]


print(f"Samples measured: {SAMPLES}")
print(f"Mean latency: {statistics.mean(latencies_ms):.2f} ms")
print(f"p50 latency: {percentile(latencies_ms, 50):.2f} ms")
print(f"p90 latency: {percentile(latencies_ms, 90):.2f} ms")
print(f"p99 latency: {percentile(latencies_ms, 99):.2f} ms")
print(f"Maximum latency: {max(latencies_ms):.2f} ms")