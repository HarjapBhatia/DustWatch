import os
from typing import Any, Dict, List, Optional

import ee
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split


def extract_features(
	candidates: Dict[str, Any],
	composite_image: ee.Image,
) -> np.ndarray:
	candidates_fc = ee.FeatureCollection(candidates)
	reduced = composite_image.reduceRegions(
		reducer=ee.Reducer.mean(),
		collection=candidates_fc,
		scale=20,
	)
	data = reduced.getInfo()

	features: List[List[float]] = []
	for feature in data.get("features", []):
		props = feature.get("properties", {})
		features.append(
			[
				float(props.get("NDVI", 0.0)),
				float(props.get("NDBI", 0.0)),
				float(props.get("BSI", 0.0)),
				float(props.get("VV", 0.0)),
				float(props.get("VH", 0.0)),
			]
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


def load_classifier(
	model_path: str = "data/models/rf_model.pkl",
) -> Optional[RandomForestClassifier]:
	if not os.path.exists(model_path):
		print(f"Warning: model file not found at {model_path}")
		return None

	return joblib.load(model_path)


def run_inference(
	features: np.ndarray,
	model_path: str = "data/models/rf_model.pkl",
) -> np.ndarray:
	if features is None or len(features) == 0:
		return np.array([])

	if features.ndim == 1:
		features = features.reshape(1, -1)

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
