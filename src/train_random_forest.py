from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from nsl_kdd_schema import NSL_KDD_COLUMNS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train and evaluate Random Forest on NSL-KDD"
    )
    parser.add_argument(
        "--train-path",
        default="data/KDDTrain+.txt",
        help="Path to NSL-KDD train file",
    )
    parser.add_argument(
        "--test-path",
        default="data/KDDTest+.txt",
        help="Path to NSL-KDD test file",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs",
        help="Directory to save metrics and plots",
    )
    parser.add_argument(
        "--artifacts-dir",
        default="artifacts",
        help="Directory to save trained model",
    )
    parser.add_argument(
        "--estimators",
        type=int,
        default=300,
        help="Number of trees in Random Forest",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=None,
        help="Max depth for trees (default: None)",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Random seed",
    )
    return parser.parse_args()


def load_nsl_kdd(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset file not found: {path}. Put NSL-KDD files under data/"
        )

    return pd.read_csv(path, header=None, names=NSL_KDD_COLUMNS)


def to_binary_target(labels: pd.Series) -> pd.Series:
    return labels.apply(lambda x: "normal" if str(x).strip() == "normal" else "attack")


def build_pipeline(
    numeric_columns: list[str],
    categorical_columns: list[str],
    estimators: int,
    max_depth: int | None,
    random_state: int,
) -> Pipeline:
    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_columns),
            ("cat", categorical_transformer, categorical_columns),
        ]
    )

    clf = RandomForestClassifier(
        n_estimators=estimators,
        max_depth=max_depth,
        random_state=random_state,
        n_jobs=-1,
        class_weight="balanced_subsample",
    )

    return Pipeline(steps=[("preprocessor", preprocessor), ("classifier", clf)])


def save_metrics(
    output_dir: Path,
    y_true: pd.Series,
    y_pred: pd.Series,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    accuracy = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, average="weighted")

    report = classification_report(y_true, y_pred)
    cm = confusion_matrix(y_true, y_pred, labels=["normal", "attack"])

    metrics_path = output_dir / "metrics.txt"
    with metrics_path.open("w", encoding="utf-8") as f:
        f.write(f"Accuracy: {accuracy:.6f}\n")
        f.write(f"Weighted F1: {f1:.6f}\n\n")
        f.write("Classification Report:\n")
        f.write(report)

    plt.figure(figsize=(6, 5))
    disp = ConfusionMatrixDisplay(cm, display_labels=["normal", "attack"])
    disp.plot(cmap="Blues", values_format="d")
    plt.title("Confusion Matrix - Random Forest (NSL-KDD)")
    plt.tight_layout()
    plt.savefig(output_dir / "confusion_matrix.png", dpi=200)
    plt.close()


def save_feature_importance_plot(model: Pipeline, output_dir: Path, top_n: int = 20) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    preprocessor: ColumnTransformer = model.named_steps["preprocessor"]
    classifier: RandomForestClassifier = model.named_steps["classifier"]

    feature_names = preprocessor.get_feature_names_out()
    importances = classifier.feature_importances_

    importance_df = (
        pd.DataFrame({"feature": feature_names, "importance": importances})
        .sort_values("importance", ascending=False)
        .head(top_n)
    )

    plt.figure(figsize=(10, 7))
    sns.barplot(data=importance_df, x="importance", y="feature", palette="viridis")
    plt.title(f"Top {top_n} Feature Importances")
    plt.xlabel("Importance")
    plt.ylabel("Feature")
    plt.tight_layout()
    plt.savefig(output_dir / "feature_importance_top20.png", dpi=200)
    plt.close()


def main() -> None:
    args = parse_args()

    train_path = Path(args.train_path)
    test_path = Path(args.test_path)
    output_dir = Path(args.output_dir)
    artifacts_dir = Path(args.artifacts_dir)

    print("Loading datasets...")
    train_df = load_nsl_kdd(train_path)
    test_df = load_nsl_kdd(test_path)

    x_train = train_df.drop(columns=["label", "difficulty"])
    y_train = to_binary_target(train_df["label"])

    x_test = test_df.drop(columns=["label", "difficulty"])
    y_test = to_binary_target(test_df["label"])

    categorical_columns = ["protocol_type", "service", "flag"]
    numeric_columns = [col for col in x_train.columns if col not in categorical_columns]

    model = build_pipeline(
        numeric_columns=numeric_columns,
        categorical_columns=categorical_columns,
        estimators=args.estimators,
        max_depth=args.max_depth,
        random_state=args.random_state,
    )

    print("Training Random Forest model...")
    model.fit(x_train, y_train)

    print("Running predictions...")
    y_pred = model.predict(x_test)

    print("Saving metrics and plots...")
    save_metrics(output_dir, y_test, y_pred)
    save_feature_importance_plot(model, output_dir, top_n=20)

    artifacts_dir.mkdir(parents=True, exist_ok=True)
    model_path = artifacts_dir / "random_forest_nids.pkl"
    joblib.dump(model, model_path)

    sample_predictions = pd.DataFrame(
        {
            "actual": y_test.reset_index(drop=True),
            "predicted": pd.Series(y_pred),
        }
    ).head(25)
    sample_predictions.to_csv(output_dir / "sample_predictions.csv", index=False)

    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average="weighted")
    print(f"Done. Accuracy: {accuracy:.4f} | Weighted F1: {f1:.4f}")
    print(f"Metrics file: {output_dir / 'metrics.txt'}")
    print(f"Confusion matrix plot: {output_dir / 'confusion_matrix.png'}")
    print(f"Feature importance plot: {output_dir / 'feature_importance_top20.png'}")
    print(f"Model artifact: {model_path}")


if __name__ == "__main__":
    main()
