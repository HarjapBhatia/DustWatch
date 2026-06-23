import os
from typing import Any, Dict, List, Optional

import ee
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split


TEMPORAL_FEATURE_NAMES = [
	"BSI_month1", "BSI_month2", "BSI_month3",
	"BSI_trend", "BSI_consistency", "BSI_variance",
	"NDVI_trend",
	"NDBI_month1", "NDBI_month2", "NDBI_month3",
	"NDBI_trend",
	"MNDWI_min",
	"VV_month1", "VV_month2", "VV_month3",
	"VV_trend", "VV_consistency",
	"VH_VV_ratio_change",
	"VV_VH_diff_month1", "VV_VH_diff_month3",
	"VV_VH_diff_trend",
]
N_FEATURES = len(TEMPORAL_FEATURE_NAMES)  # 21


def extract_features(
	candidates: Dict[str, Any],
	temporal_image: ee.Image,
) -> np.ndarray:
	candidates_fc = ee.FeatureCollection(candidates)
	reduced = temporal_image.reduceRegions(
		reducer=ee.Reducer.mean(),
		collection=candidates_fc,
		scale=20,
	)
	data = reduced.getInfo()

	features: List[List[float]] = []
	for feature in data.get("features", []):
		props = feature.get("properties", {})
		features.append(
			[float(props.get(name, 0.0)) for name in TEMPORAL_FEATURE_NAMES]
		)

	return np.array(features, dtype=float)


def train_classifier(
	features: np.ndarray,
	labels: np.ndarray,
	save_path: str = "data/models/rf_model.pkl",
) -> RandomForestClassifier:
	x_train, x_test, y_train, y_test = train_test_split(
		features,
		labels,
		test_size=0.2,
		random_state=42,
	)

	model = RandomForestClassifier(
		n_estimators=200,
		max_depth=15,
		random_state=42,
		n_jobs=-1,
	)
	model.fit(x_train, y_train)

	predictions = model.predict(x_test)
	print(classification_report(y_test, predictions))

	os.makedirs(os.path.dirname(save_path), exist_ok=True)
	joblib.dump(model, save_path)

	return model


_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_classifier(
	model_path: str = "data/models/rf_model.pkl",
) -> Optional[RandomForestClassifier]:
	primary_path = os.path.join(_BASE_DIR, "data/models/rf_construction_model.pkl")
	resolved_model_path = model_path if os.path.isabs(model_path) else os.path.join(_BASE_DIR, model_path)
	
	candidates = [
		primary_path,
		resolved_model_path,
	]
	for path in candidates:
		if os.path.exists(path):
			return joblib.load(path)
	print(f"Warning: no model file found (tried {candidates})")
	return None


def run_inference(
	features: np.ndarray,
	model_path: str = "data/models/rf_model.pkl",
) -> np.ndarray:
	if features is None or len(features) == 0:
		return np.array([])

	if features.ndim == 1:
		features = features.reshape(1, -1)

	if features.shape[1] != N_FEATURES:
		print(
			f"Warning: expected {N_FEATURES} features, got {features.shape[1]}. "
			"Padding with zeros."
		)
		pad = np.zeros((features.shape[0], N_FEATURES), dtype=float)
		cols = min(features.shape[1], N_FEATURES)
		pad[:, :cols] = features[:, :cols]
		features = pad

	model = load_classifier(model_path)
	if model is None:
		return np.full(features.shape[0], 0.5, dtype=float)

	probabilities = model.predict_proba(features)
	return probabilities[:, 1]


def filter_by_confidence(
	candidates: List[Dict[str, Any]],
	scores: np.ndarray,
	threshold: float = 0.5,
) -> List[Dict[str, Any]]:
	filtered: List[Dict[str, Any]] = []
	for site, score in zip(candidates, scores):
		rounded = round(float(score), 3)
		site["confidenceScore"] = rounded
		if rounded > threshold:
			filtered.append(site)

	return filtered
