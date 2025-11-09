"""Tests for metrics functionality. Tests files are not documented by choice."""

from unittest import mock

from app.metrics import running_scores, update_metrics


def test_update_metrics():
    """Test update_metrics function."""    
    with mock.patch("app.metrics.predictions_total") as mock_total:
        with mock.patch("app.metrics.prediction_score_histogram") as mock_hist:
            with mock.patch("app.metrics.low_score_predictions") as mock_low:
                # Clear running scores
                running_scores.clear()
                
                # Test with high score
                update_metrics(0.8)
                mock_total.inc.assert_called()
                mock_hist.observe.assert_called_with(0.8)
                mock_low.inc.assert_not_called()
                
                # Test with low score
                update_metrics(0.3)
                mock_low.inc.assert_called()


def test_update_metrics_with_many_scores():
    """Test update_metrics when running_scores exceeds 1000 items."""
    # Fill running_scores with 1001 items to trigger pop(0)
    running_scores.clear()
    for i in range(1001):
        running_scores.append(0.5)
    
    # Update metrics should pop the first item
    update_metrics(score=0.9)
    
    # Verify the list was trimmed
    assert len(running_scores) == 1001  # Should have popped one and added one
