import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import shutil

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split

from services.classifier import TEMPORAL_FEATURE_NAMES

_BACKEND = os.path.join(os.path.dirname(__file__), "..")
TRAINING_CSV    = os.path.join(_BACKEND, "data/labels/vadodara_real_training_data.csv")
MODEL_PRIMARY   = os.path.join(_BACKEND, "data/models/rf_construction_model.pkl")
MODEL_SECONDARY = os.path.join(_BACKEND, "data/models/rf_model.pkl")

# VH/VV ratio change is noisy when a monthly SAR composite has near-zero VV
# (very smooth water surface → near-zero denominator).  Cap at ±2 to prevent
# a handful of extreme values from dominating the splits.
VH_VV_CLIP = 2.0

# ---------------------------------------------------------------------------
# Load real training data
# ---------------------------------------------------------------------------

print(f"Loading training data from {TRAINING_CSV}...")
df = pd.read_csv(TRAINING_CSV)
print(f"  Rows loaded : {len(df)}")
print(f"  Class counts: {df['class'].value_counts().to_dict()}")

# Clip VH_VV_ratio_change outliers
df["VH_VV_ratio_change"] = df["VH_VV_ratio_change"].clip(-VH_VV_CLIP, VH_VV_CLIP)

X = df[TEMPORAL_FEATURE_NAMES].to_numpy(dtype=np.float32)
y = df["label"].to_numpy(dtype=np.int64)

print(f"\n  Feature matrix : {X.shape}")
print(f"  Label balance  : {dict(zip(*np.unique(y, return_counts=True)))}")

# ---------------------------------------------------------------------------
# Hold-out test split (stratified to preserve 1:2 ratio)
# ---------------------------------------------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)
print(f"\n  Train : {len(X_train)} samples")
print(f"  Test  : {len(X_test)} samples")

# ---------------------------------------------------------------------------
# Train
# ---------------------------------------------------------------------------

print("\nTraining RandomForestClassifier...")
model = RandomForestClassifier(
    n_estimators=400,
    max_depth=10,
    min_samples_leaf=2,
    class_weight="balanced",   # corrects 1:2 class imbalance
    random_state=42,
    n_jobs=-1,
)
model.fit(X_train, y_train)

# ---------------------------------------------------------------------------
# Evaluate on hold-out test set
# ---------------------------------------------------------------------------

print("\nClassification report on hold-out test set:")
y_pred = model.predict(X_test)
print(classification_report(
    y_test, y_pred,
    target_names=["false_positive", "construction"],
    digits=3,
))

# ---------------------------------------------------------------------------
# 5-fold cross-validation on the full dataset
# (better estimate with only 201 samples)
# ---------------------------------------------------------------------------

print("5-fold cross-validation on full dataset:")
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
y_cv_pred = cross_val_predict(model, X, y, cv=cv)
print(classification_report(
    y, y_cv_pred,
    target_names=["false_positive", "construction"],
    digits=3,
))

# ---------------------------------------------------------------------------
# Feature importances
# ---------------------------------------------------------------------------

importances = model.feature_importances_
ranked = sorted(zip(TEMPORAL_FEATURE_NAMES, importances), key=lambda x: x[1], reverse=True)
print("Feature importances (ranked):")
for name, imp in ranked:
    bar = "█" * int(imp * 60)
    print(f"  {name:<25} {imp:.4f}  {bar}")

# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------

os.makedirs("data/models", exist_ok=True)
joblib.dump(model, MODEL_PRIMARY)
shutil.copy2(MODEL_PRIMARY, MODEL_SECONDARY)

print(f"\nModel saved  → {MODEL_PRIMARY}")
print(f"Model copied → {MODEL_SECONDARY}")
