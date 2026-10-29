"""Deterministic examples: no downloads, private data, or fitted-data leakage."""
from pathlib import Path
import argparse
import json

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (average_precision_score, confusion_matrix, f1_score,
                             mean_absolute_error, mean_squared_error, roc_auc_score,
                             silhouette_score, adjusted_rand_score)
from sklearn.model_selection import train_test_split, TimeSeriesSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

SEED = 42


def churn_data(n=2000):
    """Synthetic customers generated from a noisy, documented probability model."""
    rng = np.random.default_rng(SEED)
    tenure = rng.integers(1, 73, n)
    charge = rng.uniform(20, 120, n)
    tickets = rng.poisson(1.2, n)
    contract = rng.choice(["monthly", "annual"], n, p=[.65, .35])
    logits = -1.1 - .035 * tenure + .012 * charge + .48 * tickets + .85 * (contract == "monthly")
    target = rng.binomial(1, 1 / (1 + np.exp(-logits)))
    data = pd.DataFrame(dict(tenure=tenure, monthly_charge=charge,
                             support_tickets=tickets, contract=contract, churn=target))
    data.loc[rng.choice(n, n // 30, replace=False), "monthly_charge"] = np.nan
    return data


def churn(data=None):
    data = churn_data() if data is None else data.copy()
    columns = ["tenure", "monthly_charge", "support_tickets", "contract", "churn"]
    if set(columns) - set(data):
        raise ValueError(f"CSV requires {columns}")
    if len(data) < 100 or set(data.churn.dropna().unique()) != {0, 1} or data.churn.isna().any():
        raise ValueError("Need at least 100 rows and a complete binary churn target")
    x = data.drop(columns="churn")[columns[:-1]]
    train_x, test_x, train_y, test_y = train_test_split(x, data.churn,
        test_size=.2, stratify=data.churn, random_state=SEED)
    train_x, val_x, train_y, val_y = train_test_split(train_x, train_y,
        test_size=.25, stratify=train_y, random_state=SEED)
    numeric = ["tenure", "monthly_charge", "support_tickets"]
    transform = ColumnTransformer([
        ("numeric", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), numeric),
        ("category", make_pipeline(SimpleImputer(strategy="most_frequent"),
            OneHotEncoder(handle_unknown="ignore")), ["contract"]),
    ])
    model = make_pipeline(transform, LogisticRegression(max_iter=1000, random_state=SEED))
    model.fit(train_x, train_y)
    val_p = model.predict_proba(val_x)[:, 1]
    thresholds = np.arange(.1, .91, .05)
    threshold = float(max(thresholds, key=lambda t: f1_score(val_y, val_p >= t)))
    probabilities = model.predict_proba(test_x)[:, 1]
    predictions = probabilities >= threshold
    baseline = DummyClassifier(strategy="prior").fit(train_x, train_y)
    importance = permutation_importance(model, test_x, test_y,
        scoring="roc_auc", n_repeats=5, random_state=SEED)
    metrics = dict(roc_auc=float(roc_auc_score(test_y, probabilities)),
        average_precision=float(average_precision_score(test_y, probabilities)),
        f1=float(f1_score(test_y, predictions)),
        baseline_average_precision=float(average_precision_score(test_y, baseline.predict_proba(test_x)[:, 1])),
        threshold=threshold, confusion_matrix=confusion_matrix(test_y, predictions).tolist(),
        train_rows=len(train_x), validation_rows=len(val_x), test_rows=len(test_x),
        permutation_importance=dict(zip(x.columns, importance.importances_mean.tolist())))
    return metrics, pd.DataFrame({"actual": test_y, "probability": probabilities,
                                  "predicted": predictions.astype(int)})


def demand_data(n=560):
    rng = np.random.default_rng(SEED)
    t = np.arange(n)
    return pd.DataFrame({"date": pd.date_range("2024-01-01", periods=n),
        "demand": np.maximum(0, 60 + .05*t + 18*np.sin(2*np.pi*t/7) + rng.normal(0, 6, n))})


def demand(data=None):
    data = demand_data() if data is None else data.copy()
    if not {"date", "demand"}.issubset(data):
        raise ValueError("CSV requires date,demand")
    data["date"] = pd.to_datetime(data.date, errors="raise")
    data = data.sort_values("date").reset_index(drop=True)
    if len(data) < 140 or data.date.duplicated().any() or data.demand.isna().any():
        raise ValueError("Need at least 140 unique daily rows with no missing demand")
    if not (data.date.diff().dropna() == pd.Timedelta(days=1)).all():
        raise ValueError("Dates must be consecutive daily observations")
    if not np.isfinite(data.demand.astype(float)).all() or (data.demand < 0).any():
        raise ValueError("Demand must be finite and nonnegative")
    frame = data.copy()
    for lag in [1, 7, 14, 28]:
        frame[f"lag_{lag}"] = frame.demand.shift(lag)
    frame["rolling_7"] = frame.demand.shift(1).rolling(7).mean()
    frame["day_sin"] = np.sin(2*np.pi*frame.date.dt.day_of_week/7)
    frame["day_cos"] = np.cos(2*np.pi*frame.date.dt.day_of_week/7)
    frame = frame.dropna().reset_index(drop=True)
    features = [c for c in frame if c not in ["date", "demand"]]
    train, test = frame.iloc[:-56], frame.iloc[-56:]
    scores = {}
    for alpha in [.1, 1, 10, 100]:
        errors = []
        for a, b in TimeSeriesSplit(n_splits=4).split(train):
            model = make_pipeline(StandardScaler(), Ridge(alpha=alpha))
            model.fit(train.iloc[a][features], train.iloc[a].demand)
            errors.append(mean_absolute_error(train.iloc[b].demand,
                model.predict(train.iloc[b][features]).clip(0)))
        scores[alpha] = float(np.mean(errors))
    alpha = min(scores, key=scores.get)
    model = make_pipeline(StandardScaler(), Ridge(alpha=alpha)).fit(train[features], train.demand)
    prediction = model.predict(test[features]).clip(0)
    baseline = test.lag_7.to_numpy()
    metrics = dict(mae=float(mean_absolute_error(test.demand, prediction)),
        rmse=float(np.sqrt(mean_squared_error(test.demand, prediction))),
        seasonal_baseline_mae=float(mean_absolute_error(test.demand, baseline)),
        selected_alpha=alpha, cv_mae=scores, train_rows=len(train), test_rows=len(test),
        evaluation="Rolling one-day-ahead: previous observed days are available; not a 56-day forecast")
    return metrics, pd.DataFrame({"date": test.date, "actual": test.demand,
                                  "prediction": prediction, "seasonal_baseline": baseline})


def transaction_data(n=300):
    rng = np.random.default_rng(SEED)
    rows = []
    snapshot = pd.Timestamp("2026-01-01")
    for customer in range(n):
        group = customer % 3
        orders = int(rng.integers([2, 7, 15][group], [5, 12, 24][group]))
        last = int(rng.integers([90, 25, 1][group], [180, 70, 20][group]))
        for order in range(orders):
            date = snapshot - pd.Timedelta(days=last + order * int(rng.integers(3, 8)))
            rows.append(dict(customer_id=f"C{customer:04}", date=date,
                amount=round(float(rng.uniform([10, 50, 150][group], [60, 150, 400][group])), 2)))
    return pd.DataFrame(rows)


def segments(data=None, snapshot="2026-01-01"):
    data = transaction_data() if data is None else data.copy()
    if not {"customer_id", "date", "amount"}.issubset(data):
        raise ValueError("CSV requires customer_id,date,amount")
    data["date"] = pd.to_datetime(data.date, errors="raise")
    cutoff = pd.Timestamp(snapshot)
    if data.isna().any().any() or not np.isfinite(data.amount).all() or (data.amount <= 0).any() or (data.date >= cutoff).any():
        raise ValueError("Transactions must be complete, positive, finite and earlier than snapshot")
    rfm = data.groupby("customer_id").agg(last_order=("date", "max"),
        frequency=("amount", "size"), monetary=("amount", "sum"))
    rfm["recency"] = (cutoff - rfm.pop("last_order")).dt.days
    features = ["recency", "frequency", "monetary"]
    if len(rfm) < 20 or rfm[features].drop_duplicates().shape[0] < 7:
        raise ValueError("Need 20 customers and at least 7 distinct RFM profiles")
    scaler = StandardScaler()
    transformed = scaler.fit_transform(np.log1p(rfm[features]))
    scores, fits = {}, {}
    for k in range(2, 7):
        fits[k] = KMeans(n_clusters=k, n_init=10, random_state=SEED).fit(transformed)
        scores[k] = float(silhouette_score(transformed, fits[k].labels_))
    best = max(scores, key=scores.get)
    model = fits[best]
    repeat = KMeans(n_clusters=best, n_init=10, random_state=7).fit(transformed)
    rfm["segment"] = model.labels_
    summary = rfm.groupby("segment")[features].mean().round(2).to_dict("index")
    metrics = dict(chosen_k=best, silhouette=scores[best], candidate_scores=scores,
        seed_stability_ari=float(adjusted_rand_score(model.labels_, repeat.labels_)),
        customers=len(rfm), snapshot=str(cutoff.date()), segment_profiles=summary)
    return metrics, rfm.reset_index()


def run(project, output="reports", csv=None, snapshot="2026-01-01"):
    data = pd.read_csv(csv) if csv else None
    functions = {"churn": churn, "demand": demand, "segments": segments}
    metrics, predictions = (segments(data, snapshot) if project == "segments" else functions[project](data))
    metrics["data_source"] = "user CSV" if csv else "synthetic demonstration data; not real-world validation"
    path = Path(output) / project
    path.mkdir(parents=True, exist_ok=True)
    (path / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    predictions.to_csv(path / "results.csv", index=False)
    print(json.dumps(metrics, indent=2))
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", choices=["churn", "demand", "segments"])
    parser.add_argument("--csv")
    parser.add_argument("--snapshot", default="2026-01-01")
    parser.add_argument("--output", default="reports")
    args = parser.parse_args()
    run(args.project, args.output, args.csv, args.snapshot)
