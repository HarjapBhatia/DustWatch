import json

import config


# -----------------------------
# Setup
# -----------------------------

config.ensure_dirs()

positive_count = 100
negative_count = 100

print("Creating starter weak labels...")
print(f"Patch index: {config.PATCHES_INDEX_JSON}")
print(f"Labels output: {config.LABELS_JSON}")

if not config.PATCHES_INDEX_JSON.exists():
    raise FileNotFoundError(
        f"Missing patch index: {config.PATCHES_INDEX_JSON}. "
        "Run extract_patches.py first."
    )


# -----------------------------
# Load Ranked Patches
# -----------------------------

with open(config.PATCHES_INDEX_JSON, "r", encoding="utf-8") as f:
    patches = json.load(f)

if len(patches) < positive_count + negative_count:
    raise ValueError(
        f"Need at least {positive_count + negative_count} patches, found {len(patches)}."
    )


# -----------------------------
# Build Weak Labels
# -----------------------------

# The index is sorted by high DELTA_BSI and low DELTA_NDVI, so the top patches
# are likely exposed-soil change candidates. These are weak positives.
positive_candidates = patches[:positive_count]

# The bottom patches are least construction-like by the same heuristic. These
# are weak negatives.
negative_candidates = patches[-negative_count:]

labels = []

for item in positive_candidates:
    labels.append(
        {
            "patch": item["patch"],
            "label": 1,
        }
    )

for item in negative_candidates:
    labels.append(
        {
            "patch": item["patch"],
            "label": 0,
        }
    )


# -----------------------------
# Save Labels
# -----------------------------

with open(config.LABELS_JSON, "w", encoding="utf-8") as f:
    json.dump(labels, f, indent=2)

print(f"Saved starter labels: {config.LABELS_JSON}")
print(f"Construction weak labels: {positive_count}")
print(f"Non-construction weak labels: {negative_count}")
print("Review these labels manually before trusting model results.")
