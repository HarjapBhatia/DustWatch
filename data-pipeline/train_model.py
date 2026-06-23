import json
import math
from collections import Counter

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

import config


# Setup
config.ensure_dirs()

print("Starting Random Forest training...")
print(f"Labels file: {config.LABELS_JSON}")
print(f"Patches folder: {config.PATCHES_DIR}")
print(f"Model output: {config.MODEL_PATH}")

if not config.LABELS_JSON.exists():
    raise FileNotFoundError(
        f"Missing labels file: {config.LABELS_JSON}. "
        "Create it with entries like "
        '[{"patch": "patch_row0_col256.npy", "label": 1}].'
    )



# Load Labels
with open(config.LABELS_JSON, "r", encoding="utf-8") as f:
    labels = json.load(f)

if not labels:
    raise ValueError("labels.json is empty. Add labeled patches before training.")

print(f"Loaded labels: {len(labels)}")


# Feature Extraction

features = []
targets = []

for item in labels:
    patch_name = item["patch"]
    label = int(item["label"])
    patch_path = config.PATCHES_DIR / patch_name

    if label not in [0, 1]:
        raise ValueError(f"Invalid label for {patch_name}: {label}. Use 0 or 1.")

    if not patch_path.exists():
        raise FileNotFoundError(f"Missing patch file referenced by labels: {patch_path}")

    patch = np.load(patch_path)

    if patch.shape[0] != len(config.BAND_NAMES):
        raise ValueError(
            f"{patch_name} has {patch.shape[0]} bands, expected {len(config.BAND_NAMES)}."
        )

    patch = np.nan_to_num(patch, nan=0.0, posinf=0.0, neginf=0.0)
    feature_vector = patch.mean(axis=(1, 2))

    features.append(feature_vector)
    targets.append(label)

X = np.asarray(features, dtype=np.float32)
y = np.asarray(targets, dtype=np.int64)

class_counts = Counter(y.tolist())
print(f"Class counts: {dict(class_counts)}")

if len(class_counts) < 2:
    raise ValueError("Need both classes in labels.json: 1=construction and 0=non-construction.")

if min(class_counts.values()) < 2:
    raise ValueError("Need at least 2 samples per class for a stratified train/test split.")


# Train/Test Split

print("Splitting train/test data...")
test_count = max(len(class_counts), math.ceil(len(y) * 0.2))

if len(y) - test_count < len(class_counts):
    raise ValueError(
        "Not enough labeled samples for a stratified train/test split. "
        "Add more labels so both train and test sets can contain both classes."
    )

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=test_count,
    stratify=y,
    random_state=42,
)


# Train Model

print("Training RandomForestClassifier...")
model = RandomForestClassifier(
    n_estimators=200,
    max_depth=15,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1,
)
model.fit(X_train, y_train)


# Evaluate

print("Evaluating model...")
y_pred = model.predict(X_test)
print(classification_report(y_test, y_pred, target_names=["non_construction", "construction"]))


# Feature Importance

importances = [
    {"feature": name, "importance": float(score)}
    for name, score in zip(config.BAND_NAMES, model.feature_importances_)
]
importances.sort(key=lambda item: item["importance"], reverse=True)

print("Feature importances:")
for item in importances:
    print(f"  {item['feature']}: {item['importance']:.4f}")


# Save Outputs

joblib.dump(model, config.MODEL_PATH)

with open(config.FEATURE_IMPORTANCE_JSON, "w", encoding="utf-8") as f:
    json.dump(importances, f, indent=2)

print(f"Saved model: {config.MODEL_PATH}")
print(f"Saved feature importances: {config.FEATURE_IMPORTANCE_JSON}")
