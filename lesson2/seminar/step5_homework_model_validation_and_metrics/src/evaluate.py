import json
import os
import pickle

import pandas as pd
import yaml
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split


def load_params():
    with open("params.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def evaluate_model():
    params = load_params()

    with open("models/model.pkl", "rb") as f:
        model = pickle.load(f)

    df = pd.read_csv("data/processed/dataset.csv")
    X = df[["total_bill", "size"]]
    y = df["high_tip"]

    _, X_test, _, y_test = train_test_split(
        X, y, test_size=params["test_size"], random_state=params["seed"]
    )

    accuracy = float(accuracy_score(y_test, model.predict(X_test)))
    metrics = {"accuracy": accuracy, "rows": int(len(df))}

    os.makedirs("metrics", exist_ok=True)
    with open("metrics/metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print(metrics)


if __name__ == "__main__":
    evaluate_model()
