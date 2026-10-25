
import argparse
import json
import random
from collections import Counter
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_FILE = ROOT / "data" / "synthetic_events.jsonl"

EVENT_COUNT = 500
RANDOM_SEED = 20261025

OUTCOME_COUNTS = {
    "success": 300,
    "failed_downstream": 100,
    "abandoned": 75,
    "escalated": 25,
}


def calls_per_minute(minute_of_day: int) -> float:
    """Return the target traffic rate for a minute in the 24-hour profile."""
    hour = minute_of_day // 60
    minute_in_hour = minute_of_day % 60

    # Baseline periods: 00:00–08:00, 10:00–14:00, 16:00–24:00.
    if hour < 8 or 10 <= hour < 14 or hour >= 16:
        return 10.0

    # Campaign periods: 08:00–10:00 and 14:00–16:00.
    # Ramp from 10 to 50 calls/minute during the first 15 minutes.
    if hour in (8, 14) and minute_in_hour < 15:
        return 10.0 + 40.0 * (minute_in_hour + 1) / 15.0

    return 50.0


def make_timestamps(
    rng: random.Random,
    count: int,
    simulation_date: date,
) -> list[datetime]:
    """Sample event times using the relative intensity of each traffic minute."""
    minutes = list(range(24 * 60))
    weights = [calls_per_minute(minute) for minute in minutes]

    selected_minutes = rng.choices(
        minutes,
        weights=weights,
        k=count,
    )

    timestamps = []
    day_start = datetime.combine(
        simulation_date,
        time.min,
        tzinfo=timezone.utc,
    )

    for minute in selected_minutes:
        second = rng.randrange(60)
        microsecond = rng.randrange(1_000_000)

        timestamp = (
            day_start
            + timedelta(
                minutes=minute,
                seconds=second,
                microseconds=microsecond,
            )
        )
        timestamps.append(timestamp)

    return sorted(timestamps)


def campaign_for(timestamp: datetime) -> str:
    """Classify an event by its position in the traffic profile."""
    hour = timestamp.hour

    if 8 <= hour < 10:
        return "campaign_morning"
    if 14 <= hour < 16:
        return "campaign_afternoon"
    return "baseline"


def generate_events(
    count: int = EVENT_COUNT,
    seed: int = RANDOM_SEED,
    simulation_date: date = date(2026, 1, 1),
) -> list[dict]:
    """Create a reproducible dataset of synthetic pipeline events."""
    if count != EVENT_COUNT:
        raise ValueError(
            f"This assignment dataset must contain exactly {EVENT_COUNT} events."
        )

    rng = random.Random(seed)

    outcomes = []
    for outcome, outcome_count in OUTCOME_COUNTS.items():
        outcomes.extend([outcome] * outcome_count)

    rng.shuffle(outcomes)

    timestamps = make_timestamps(rng, count, simulation_date)

    borrower_buckets = ["bucket_1", "bucket_2", "bucket_3"]
    product_types = [
        "personal_loan",
        "vehicle_loan",
        "business_loan",
    ]

    events = []

    for index, (timestamp, outcome) in enumerate(
        zip(timestamps, outcomes),
        start=1,
    ):
        if outcome == "failed_downstream":
            retry_count = 3
        elif outcome == "success":
            retry_count = rng.choices([0, 1, 2], weights=[80, 15, 5])[0]
        elif outcome == "escalated":
            retry_count = rng.choice([0, 1, 2])
        else:
            retry_count = 0

        call_duration_s = (
            rng.randint(15, 600)
            if outcome != "abandoned"
            else rng.randint(1, 90)
        )

        event = {
            "event_id": f"synthetic-{index:04d}",
            "campaign_id": campaign_for(timestamp),
            "borrower_bucket": rng.choice(borrower_buckets),
            "timestamp": timestamp.isoformat().replace("+00:00", "Z"),
            "outcome": outcome,
            "properties": {
                "product_type": rng.choice(product_types),
                "call_duration_s": call_duration_s,
                "retry_count": retry_count,
            },
        }

        events.append(event)

    return events


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate the reproducible 500-event assignment dataset."
    )
    parser.add_argument(
        "--date",
        default="2026-01-01",
        help="UTC simulation date in YYYY-MM-DD format (default: 2026-01-01)",
    )
    parser.add_argument(
        "--output",
        default=str(OUTPUT_FILE),
        help="Output JSONL path",
    )
    args = parser.parse_args()

    simulation_date = date.fromisoformat(args.date)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    events = generate_events(simulation_date=simulation_date)

    with output_path.open("w", encoding="utf-8", newline="\n") as file:
        for event in events:
            file.write(json.dumps(event, separators=(",", ":")) + "\n")

    counts = Counter(event["outcome"] for event in events)

    print(f"Generated {len(events)} events")
    print(f"Output: {output_path}")
    print(f"Seed: {RANDOM_SEED}")
    print(f"Simulation date (UTC): {simulation_date.isoformat()}")
    print("Outcome counts:")
    for outcome, count in sorted(counts.items()):
        print(f"  {outcome}: {count}")


if __name__ == "__main__":
    main()
