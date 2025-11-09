"""Prometheus metrics for monitoring."""

import typing as tp

from prometheus_client import Counter, Gauge, Histogram

from app.config import LOW_SCORE_THRESHOLD

# Prometheus metrics
prediction_score_avg = Gauge(
    "prediction_score_average",
    "Average prediction score"
)
prediction_score_histogram = Histogram(
    "prediction_score",
    "Histogram of prediction scores"
)
predictions_total = Counter(
    "predictions_total",
    "Total number of predictions"
)
low_score_predictions = Counter(
    "low_score_predictions_total",
    "Number of predictions with score below threshold"
)

# Running scores for average calculation
running_scores: tp.List[float] = []


def update_metrics(score: float) -> None:
    """Update Prometheus metrics.

    Args:
        score: Prediction confidence score
    """
    # Increment total predictions counter
    predictions_total.inc()

    # Record score in histogram
    prediction_score_histogram.observe(score)

    # Track low scores
    if score < LOW_SCORE_THRESHOLD:
        low_score_predictions.inc()

    # Update running average
    running_scores.append(score)
    # Keep only last 1000 scores to prevent memory issues
    if len(running_scores) > 1000:
        running_scores.pop(0)

    # Update average gauge
    if running_scores:
        avg_score = sum(running_scores) / len(running_scores)
        prediction_score_avg.set(avg_score)
