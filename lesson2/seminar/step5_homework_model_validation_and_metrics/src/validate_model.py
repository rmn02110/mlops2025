import json
import pickle
import sys

import pandas as pd
import yaml
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split


def load_params():
    with open("params.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def read_accuracy(params):
    try:
        with open("metrics/metrics.json", "r", encoding="utf-8") as f:
            return float(json.load(f)["accuracy"])
    except FileNotFoundError:
        with open("models/model.pkl", "rb") as f:
            model = pickle.load(f)
        df = pd.read_csv("data/processed/dataset.csv")
        X = df[["total_bill", "size"]]
        y = df["high_tip"]
        _, X_test, _, y_test = train_test_split(
            X, y, test_size=params["test_size"], random_state=params["seed"]
        )
        return float(accuracy_score(y_test, model.predict(X_test)))


def validate_model():
    params = load_params()
    accuracy = read_accuracy(params)
    accuracy_min = float(params["accuracy_min"])

    print(f"accuracy={accuracy:.4f}, accuracy_min={accuracy_min:.4f}")
    if accuracy < accuracy_min:
        sys.exit(1)


if __name__ == "__main__":
    validate_model()
