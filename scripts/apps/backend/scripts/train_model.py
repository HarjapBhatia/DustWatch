import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split


def generate_synthetic_training_data(n_samples: int = 1000) -> tuple[np.ndarray, np.ndarray]:
	n_construction = int(n_samples * 0.4)
	n_non_construction = n_samples - n_construction

	construction = np.column_stack(
		[
			np.random.uniform(-0.1, 0.2, n_construction),
			np.random.uniform(0.1, 0.5, n_construction),
			np.random.uniform(0.15, 0.6, n_construction),
			np.random.uniform(-10, -5, n_construction),
			np.random.uniform(-18, -12, n_construction),
		]
	)

	non_construction = np.column_stack(
		[
			np.random.uniform(0.2, 0.8, n_non_construction),
			np.random.uniform(-0.3, 0.1, n_non_construction),
			np.random.uniform(-0.2, 0.15, n_non_construction),
			np.random.uniform(-18, -10, n_non_construction),
			np.random.uniform(-25, -18, n_non_construction),
		]
	)

	features = np.vstack([construction, non_construction])
	labels = np.concatenate(
		[np.ones(n_construction, dtype=int), np.zeros(n_non_construction, dtype=int)]
	)

	noise = np.random.normal(0, 0.02, features.shape)
	features = features + noise

	return features, labels


def main() -> None:
	features, labels = generate_synthetic_training_data(2000)
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

	os.makedirs("data/models", exist_ok=True)
	joblib.dump(model, "data/models/rf_model.pkl")
	print("Model saved to data/models/rf_model.pkl")


if __name__ == "__main__":
	main()
