from __future__ import annotations

import json
import pickle
from pathlib import Path

import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "california_housing_prepared.csv"
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "output"


def tune_model_candidates() -> tuple[str, dict, object]:
    df = pd.read_csv(DATA_PATH)
    X = df.drop(columns=["MedHouseVal"])
    y = df["MedHouseVal"]

    X_train, X_temp, y_train, y_temp = train_test_split(
        X,
        y,
        test_size=0.30,
        random_state=42,
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp,
        y_temp,
        test_size=0.50,
        random_state=42,
    )

    candidates: list[tuple[str, dict, float, float, float]] = []

    rf_configs = [
        {"n_estimators": 100, "max_depth": None, "min_samples_leaf": 1},
        {"n_estimators": 200, "max_depth": None, "min_samples_leaf": 1},
        {"n_estimators": 300, "max_depth": None, "min_samples_leaf": 1},
        {"n_estimators": 300, "max_depth": 12, "min_samples_leaf": 1},
        {"n_estimators": 300, "max_depth": 12, "min_samples_leaf": 3},
        {"n_estimators": 200, "max_depth": 8, "min_samples_leaf": 2},
    ]
    for params in rf_configs:
        model = RandomForestRegressor(random_state=42, **params)
        model.fit(X_train, y_train)
        train_mse = mean_squared_error(y_train, model.predict(X_train))
        val_mse = mean_squared_error(y_val, model.predict(X_val))
        gap = abs(train_mse - val_mse)
        score = val_mse + 0.2 * gap
        candidates.append(("random_forest", params, score, train_mse, val_mse))

    gb_configs = [
        {"n_estimators": 200, "learning_rate": 0.05, "max_depth": 2, "subsample": 1.0},
        {"n_estimators": 300, "learning_rate": 0.05, "max_depth": 2, "subsample": 0.8},
        {"n_estimators": 500, "learning_rate": 0.05, "max_depth": 3, "subsample": 0.9},
        {"n_estimators": 600, "learning_rate": 0.03, "max_depth": 3, "subsample": 0.8},
        {"n_estimators": 300, "learning_rate": 0.05, "max_depth": 3, "subsample": 1.0},
        {"n_estimators": 800, "learning_rate": 0.02, "max_depth": 2, "subsample": 1.0},
    ]
    for params in gb_configs:
        model = GradientBoostingRegressor(random_state=42, **params)
        model.fit(X_train, y_train)
        train_mse = mean_squared_error(y_train, model.predict(X_train))
        val_mse = mean_squared_error(y_val, model.predict(X_val))
        gap = abs(train_mse - val_mse)
        score = val_mse + 0.2 * gap
        candidates.append(("gradient_boosting", params, score, train_mse, val_mse))

    best_model_name, best_params, _, best_train_mse, best_val_mse = min(
        candidates,
        key=lambda item: (item[2], item[4]),
    )

    if best_model_name == "random_forest":
        model = RandomForestRegressor(random_state=42, **best_params)
    else:
        model = GradientBoostingRegressor(random_state=42, **best_params)

    model.fit(X_train, y_train)

    test_pred = model.predict(X_test)
    test_mse = mean_squared_error(y_test, test_pred)
    test_r2 = r2_score(y_test, test_pred)

    result = {
        "best_model": best_model_name,
        "best_params": best_params,
        "train_mse": float(best_train_mse),
        "validation_mse": float(best_val_mse),
        "train_validation_gap": float(abs(best_train_mse - best_val_mse)),
        "test_mse": float(test_mse),
        "test_r2": float(test_r2),
        "split_sizes": {"train": int(len(X_train)), "validation": int(len(X_val)), "test": int(len(X_test))},
        "dataset_rows": int(len(df)),
    }

    return best_model_name, result, model


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    model_name, result, model = tune_model_candidates()

    with (OUTPUT_DIR / f"{model_name}_california_housing_model.pkl").open("wb") as fh:
        pickle.dump(model, fh)
    with (OUTPUT_DIR / "california_housing_model_metrics.json").open("w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
