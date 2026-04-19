# Random Forest NIDS (NSL-KDD)

This repository trains and evaluates a Random Forest model for network intrusion detection using the NSL-KDD dataset.

It includes:

- Binary classification (`normal` vs `attack`)
- Prediction on test data
- Accuracy and Weighted F1 score
- Confusion matrix plot
- Feature importance plot
- Trained model artifact (`.pkl`)

## Project Structure

```text
zaid_ds_network_prj/
	src/
		nsl_kdd_schema.py
		train_random_forest.py
	requirements.txt
	README.md
```

## 1. Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2. Add Dataset Files

Create a `data` directory and place NSL-KDD files:

- `data/KDDTrain+.txt`
- `data/KDDTest+.txt`

Example:

```powershell
mkdir data
```

## 3. Train and Evaluate (Random Forest)

```powershell
python src/train_random_forest.py --train-path data/KDDTrain+.txt --test-path data/KDDTest+.txt
```

Optional tuning example:

```powershell
python src/train_random_forest.py --estimators 500 --max-depth 30 --random-state 42
```

## 4. Expected Outputs

After training, the script creates:

- `outputs/metrics.txt`
	- Accuracy
	- Weighted F1
	- Classification report
- `outputs/confusion_matrix.png`
- `outputs/feature_importance_top20.png`
- `outputs/sample_predictions.csv`
- `artifacts/random_forest_nids.pkl`

## 5. Notebook Demo (Recommended for Presentation)

Use the step-by-step notebook:

- `nids_random_forest_demo.ipynb`

Run order in notebook:

1. Execute all cells from top to bottom.
2. If NSL-KDD files are missing, the notebook uses temporary synthetic data automatically.
3. Metrics and plots are saved automatically to the outputs folder.

What it does:

- Attempts to load real NSL-KDD data from `data/KDDTrain+.txt` and `data/KDDTest+.txt`
- Falls back to synthetic temporary data automatically if files are not found
- Trains Random Forest and computes Accuracy + Weighted F1
- Plots confusion matrix and top-20 feature importances
- Saves notebook outputs under `outputs/notebook/`

Notebook artifacts:

- `data/input_features_sample.csv` (features-only input CSV for demo predictions)
- `outputs/notebook/notebook_demo_data_preview.csv`
- `outputs/notebook/notebook_metrics.txt`
- `outputs/notebook/notebook_confusion_matrix.png`
- `outputs/notebook/notebook_feature_importance_top20.png`
- `outputs/notebook/notebook_sample_predictions.csv`
- `artifacts/random_forest_nids_notebook.pkl`

## 6. What Is Measured

- **Accuracy**: overall correct predictions
- **Weighted F1**: class-balanced quality measure
- **Confusion Matrix**: true vs predicted for `normal` and `attack`

## 7. Notes

- Categorical features (`protocol_type`, `service`, `flag`) are one-hot encoded.
- Numeric features are imputed and scaled.
- Random Forest uses `class_weight="balanced_subsample"`.
- Label mapping is binary:
	- `normal` -> `normal`
	- all other labels -> `attack`
