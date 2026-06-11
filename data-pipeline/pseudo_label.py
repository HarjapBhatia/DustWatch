import json
import joblib
import numpy as np
import config

config.ensure_dirs()

print("Starting pseudo_label.py...")
print(f"Reading model from: {config.MODEL_PATH}")
print(f"Reading labeling queue from: {config.LABELING_QUEUE_JSON}")
print(f"Saving pseudo labels to: {config.PSEUDO_LABELS_JSON}")

if not config.MODEL_PATH.exists():
    raise FileNotFoundError(
        f"Missing model file: {config.MODEL_PATH}. Train the model to above 0.75 F1 score first."
    )

if not config.LABELING_QUEUE_JSON.exists():
    raise FileNotFoundError(
        f"Missing labeling queue: {config.LABELING_QUEUE_JSON}. Run suggest_patches.py first."
    )

# Load Model
model = joblib.load(config.MODEL_PATH)
print("Model loaded successfully.")

# Load Queue
with open(config.LABELING_QUEUE_JSON, "r", encoding="utf-8") as f:
    queue = json.load(f)
print(f"Loaded {len(queue)} patches from labeling queue.")

pseudo_labels = []
manual_review_count = 0
auto_labeled_count = 0

# Confidence distribution bin setup
bins = {
    "0.50 to 0.60": 0,
    "0.60 to 0.70": 0,
    "0.70 to 0.80": 0,
    "0.80 to 0.90": 0,
    "0.90 to 1.00": 0
}

# Run predictions
for idx, item in enumerate(queue):
    patch_name = item["patch"]
    patch_path = config.PATCHES_DIR / patch_name

    if not patch_path.exists():
        print(f"Warning: Patch {patch_name} not found, skipping.")
        continue

    # Extract features
    patch = np.load(patch_path)
    patch = np.nan_to_num(patch, nan=0.0, posinf=0.0, neginf=0.0)
    feature_vector = patch.mean(axis=(1, 2)).reshape(1, -1)

    # Predict probability
    probs = model.predict_proba(feature_vector)[0]
    pred_label = int(np.argmax(probs))
    confidence = float(probs[pred_label])

    # Assign confidence to bins
    if 0.50 <= confidence < 0.60:
        bins["0.50 to 0.60"] += 1
    elif 0.60 <= confidence < 0.70:
        bins["0.60 to 0.70"] += 1
    elif 0.70 <= confidence < 0.80:
        bins["0.70 to 0.80"] += 1
    elif 0.80 <= confidence < 0.90:
        bins["0.80 to 0.90"] += 1
    elif 0.90 <= confidence <= 1.00:
        bins["0.90 to 1.00"] += 1

    # Check threshold (90%)
    if confidence > 0.90:
        pseudo_labels.append({
            "patch": patch_name,
            "label": pred_label,
            "confidence": round(confidence, 4)
        })
        auto_labeled_count += 1
    else:
        manual_review_count += 1

    if (idx + 1) % 50 == 0 or (idx + 1) == len(queue):
        print(f"Processed {idx + 1}/{len(queue)} patches...")

# Print breakdown
print("\nConfidence Distribution of Predictions:")
for bin_name, count in bins.items():
    percentage = (count / len(queue)) * 100 if queue else 0
    print(f"  {bin_name}: {count} patches ({percentage:.2f}%)")

print("\nPseudo-labeling Summary:")
print(f"  Auto-labeled (Confidence > 0.90): {auto_labeled_count}")
print(f"  Needs Manual Review:              {manual_review_count}")

# Save pseudo labels
with open(config.PSEUDO_LABELS_JSON, "w", encoding="utf-8") as f:
    json.dump(pseudo_labels, f, indent=2)

print(f"\nSaved {len(pseudo_labels)} pseudo labels to: {config.PSEUDO_LABELS_JSON}")
print("pseudo_label.py completed.")
