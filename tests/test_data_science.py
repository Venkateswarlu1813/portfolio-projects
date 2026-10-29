import numpy as np
import pytest
from portfolio.data_science import churn, churn_data, demand, demand_data, segments, transaction_data, run


def test_churn_has_held_out_performance_and_validation_threshold():
    metrics, results = churn()
    assert metrics["train_rows"] == 1200
    assert metrics["validation_rows"] == metrics["test_rows"] == 400
    assert metrics["average_precision"] > metrics["baseline_average_precision"]
    assert 0.65 < metrics["roc_auc"] < 1
    assert results.probability.between(0, 1).all()
    assert sum(map(sum, metrics["confusion_matrix"])) == 400


def test_churn_rejects_missing_or_single_class_targets():
    data = churn_data()
    data["churn"] = 0
    with pytest.raises(ValueError):
        churn(data)


def test_demand_time_holdout_and_seasonal_comparison():
    metrics, results = demand()
    assert metrics["test_rows"] == 56
    assert results.date.is_monotonic_increasing
    assert metrics["mae"] < metrics["seasonal_baseline_mae"]
    assert results.prediction.ge(0).all()


def test_demand_rejects_missing_day():
    with pytest.raises(ValueError, match="consecutive"):
        demand(demand_data().drop(index=40))


def test_rfm_segments_are_nonempty_and_stable():
    metrics, results = segments()
    assert 2 <= metrics["chosen_k"] <= 6
    assert len(results) == 300
    assert results.segment.nunique() == metrics["chosen_k"]
    assert metrics["silhouette"] > .3
    assert metrics["seed_stability_ari"] > .8


def test_rfm_snapshot_prevents_future_transactions():
    with pytest.raises(ValueError, match="snapshot"):
        segments(transaction_data(), "2024-01-01")


def test_metrics_export_labels_synthetic_data(tmp_path):
    metrics = run("demand", tmp_path)
    assert "synthetic" in metrics["data_source"]
    assert (tmp_path / "demand" / "metrics.json").exists()
    assert (tmp_path / "demand" / "results.csv").exists()
