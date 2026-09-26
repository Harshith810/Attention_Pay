from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import shap
import torch
from lime.lime_tabular import LimeTabularExplainer

from backend.app.services.explainability.human_explanation import (
    build_human_readable_explanation,
)


class TabTransformerExplainer:
    """
    Explain TabTransformer predictions using SHAP and LIME.

    Important:
    - The trained model is NOT changed.
    - The same scaler and categorical encoders used by inference are reused.
    - SHAP/LIME receive raw feature values and the prediction wrapper applies
      the exact production preprocessing before calling the model.
    - The XAI background is sampled from the real TabTransformer training data,
      not from repeated synthetic baseline rows.
    """

    DEFAULT_SHAP_BACKGROUND_SIZE = 120
    DEFAULT_LIME_BACKGROUND_SIZE = 800
    DEFAULT_LIME_SAMPLES = 3000

    def __init__(
        self,
        model: torch.nn.Module,
        scaler: Any,
        cat_encoders: dict[str, Any],
        feature_order: list[str],
        device: torch.device,
        background_path: str | Path | None = None,
        shap_background_size: int = DEFAULT_SHAP_BACKGROUND_SIZE,
        lime_background_size: int = DEFAULT_LIME_BACKGROUND_SIZE,
        lime_samples: int = DEFAULT_LIME_SAMPLES,
    ) -> None:
        self.model = model
        self.scaler = scaler
        self.cat_encoders = cat_encoders
        self.feature_order = list(feature_order)
        self.device = device
        self.lime_samples = lime_samples

        if background_path is None:
            project_root = Path(__file__).resolve().parents[4]
            background_path = (
                project_root
                / "backend"
                / "ml"
                / "tabtransformer"
                / "artifacts"
                / "xai_background.joblib"
            )

        self.background_path = Path(background_path)
        background = self._load_background(self.background_path)

        if len(background) < max(shap_background_size, lime_background_size):
            raise ValueError(
                "XAI background dataset is smaller than the requested "
                "SHAP/LIME background size."
            )

        # Keep the background in raw feature space. This is important because
        # _predict_proba() applies the production scaler/encoders itself.
        self.background = background[self.feature_order].copy()

        self.shap_background = self._sample_background(
            self.background,
            shap_background_size,
        )
        self.lime_background = self._sample_background(
            self.background,
            lime_background_size,
        )

        # SHAP operates on numeric vectors. Categorical strings are encoded
        # using the same encoders as production inference.
        shap_encoded = self._encode_dataframe(self.shap_background)
        self._shap_masker = shap.maskers.Independent(
            shap_encoded.astype(np.float64),
            max_samples=shap_background_size,
        )
        self._shap_explainer = shap.Explainer(
            self._predict_proba_encoded,
            self._shap_masker,
            algorithm="permutation",
        )

        # LIME also operates on numeric vectors. categorical_features tells
        # LIME which integer columns should be perturbed as categories.
        lime_encoded = self._encode_dataframe(self.lime_background)
        self._lime_categorical_indices = [
            index
            for index, feature in enumerate(self.feature_order)
            if feature in self.cat_encoders
        ]

        self._lime_categorical_names = {}
        for index in self._lime_categorical_indices:
            feature = self.feature_order[index]
            encoder = self.cat_encoders[feature]
            self._lime_categorical_names[index] = [
                str(value) for value in encoder.classes_
            ]

        self._lime_explainer = LimeTabularExplainer(
            training_data=lime_encoded.astype(np.float64),
            feature_names=self.feature_order,
            categorical_features=self._lime_categorical_indices,
            categorical_names=self._lime_categorical_names,
            mode="classification",
            class_names=["Fraud", "Legitimate"],
            discretize_continuous=True,
            random_state=42,
        )

    # =========================================================
    # BACKGROUND DATA
    # =========================================================

    def _load_background(self, path: Path) -> pd.DataFrame:
        if not path.exists():
            raise FileNotFoundError(
                f"XAI background artifact not found: {path}. "
                "Build xai_background.joblib from the exact TabTransformer "
                "training dataset before starting the backend."
            )

        data = joblib.load(path)
        if isinstance(data, pd.DataFrame):
            background = data.copy()
        elif isinstance(data, dict) and "data" in data:
            background = pd.DataFrame(data["data"])
        else:
            background = pd.DataFrame(data)

        missing = [
            feature
            for feature in self.feature_order
            if feature not in background.columns
        ]
        if missing:
            raise ValueError(
                f"XAI background is missing required features: {missing}"
            )

        background = background[self.feature_order].copy()

        # Validate categories before the server starts. Silent category
        # mismatches would make explanations inconsistent with inference.
        for feature, encoder in self.cat_encoders.items():
            if feature not in background.columns:
                raise ValueError(
                    f"Categorical feature '{feature}' is absent from XAI background."
                )

            known = set(str(value) for value in encoder.classes_)
            observed = set(str(value) for value in background[feature].dropna())
            unknown = sorted(observed - known)
            if unknown:
                raise ValueError(
                    f"XAI background contains unseen values for '{feature}': {unknown}"
                )

        return background.reset_index(drop=True)

    @staticmethod
    def _sample_background(
        data: pd.DataFrame,
        size: int,
    ) -> pd.DataFrame:
        if len(data) <= size:
            return data.reset_index(drop=True).copy()

        # Fixed random state makes explanations reproducible across backend
        # restarts while retaining the real training distribution.
        return data.sample(
            n=size,
            random_state=42,
        ).reset_index(drop=True)

    # =========================================================
    # PREPROCESSING
    # =========================================================

    def _encode_dataframe(self, data: pd.DataFrame) -> np.ndarray:
        encoded = np.zeros(
            (len(data), len(self.feature_order)),
            dtype=np.float64,
        )

        for index, feature in enumerate(self.feature_order):
            if feature in self.cat_encoders:
                encoder = self.cat_encoders[feature]
                values = data[feature].astype(str).to_numpy()
                encoded[:, index] = encoder.transform(values).astype(np.float64)
            else:
                encoded[:, index] = pd.to_numeric(
                    data[feature],
                    errors="raise",
                ).to_numpy(dtype=np.float64)

        return encoded

    def _vector_to_raw_dataframe(self, vector: np.ndarray) -> pd.DataFrame:
        vector = np.asarray(vector, dtype=np.float64).reshape(-1)
        if vector.shape[0] != len(self.feature_order):
            raise ValueError(
                f"Expected {len(self.feature_order)} features, "
                f"received {vector.shape[0]}"
            )

        row: dict[str, Any] = {}

        for index, feature in enumerate(self.feature_order):
            value = vector[index]

            if feature in self.cat_encoders:
                encoder = self.cat_encoders[feature]
                category_index = int(round(value))
                if category_index < 0 or category_index >= len(encoder.classes_):
                    raise ValueError(
                        f"Invalid encoded category {category_index} for '{feature}'."
                    )
                row[feature] = encoder.classes_[category_index]
            else:
                row[feature] = float(value)

        return pd.DataFrame([row], columns=self.feature_order)

    def _raw_dataframe_to_model_tensors(
        self,
        data: pd.DataFrame,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        categorical = []
        numerical = []

        categorical_features = set(self.cat_encoders.keys())
        numerical_features = [
            feature
            for feature in self.feature_order
            if feature not in categorical_features
        ]

        for feature in self.feature_order:
            if feature in categorical_features:
                encoder = self.cat_encoders[feature]
                values = encoder.transform(
                    data[feature].astype(str).to_numpy()
                )
                categorical.append(values.astype(np.int64))

        categorical_array = np.stack(categorical, axis=1)
        # Keep the exact numerical feature names when calling the fitted scaler.
        # This avoids sklearn's "X does not have valid feature names" warning
        # and guarantees the scaler receives the same column structure used
        # during model training.
        numerical_data = data[numerical_features].copy()
        numerical_array = numerical_data.to_numpy(dtype=np.float64)
        numerical_scaled = self.scaler.transform(numerical_data).astype(np.float32)

        categorical_tensor = torch.from_numpy(categorical_array).long().to(self.device)
        numerical_tensor = torch.from_numpy(numerical_scaled).float().to(self.device)

        return categorical_tensor, numerical_tensor

    # =========================================================
    # MODEL WRAPPERS
    # =========================================================

    def _predict_proba_raw(self, data: pd.DataFrame) -> np.ndarray:
        categorical, numerical = self._raw_dataframe_to_model_tensors(data)

        with torch.no_grad():
            logits = self.model(categorical, numerical)
            probabilities = torch.softmax(logits, dim=1)

        return probabilities.detach().cpu().numpy()

    def _predict_proba_encoded(self, vectors: np.ndarray) -> np.ndarray:
        vectors = np.asarray(vectors, dtype=np.float64)
        if vectors.ndim == 1:
            vectors = vectors.reshape(1, -1)

        rows = [
            self._vector_to_raw_dataframe(vector).iloc[0].to_dict()
            for vector in vectors
        ]
        data = pd.DataFrame(rows, columns=self.feature_order)
        return self._predict_proba_raw(data)

    # =========================================================
    # EXPLANATION
    # =========================================================

    def explain(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Return SHAP and LIME feature contributions for one transaction.

        Positive contribution -> pushes the prediction toward Fraud.
        Negative contribution -> pushes the prediction toward Legitimate.
        """
        raw_data = pd.DataFrame(
            [{feature: data[feature] for feature in self.feature_order}],
            columns=self.feature_order,
        )

        encoded_input = self._encode_dataframe(raw_data)
        probabilities = self._predict_proba_raw(raw_data)[0]

        # Label mapping:
        # 0 = Fraud
        # 1 = Legitimate
        fraud_probability = float(probabilities[0])
        legitimate_probability = float(probabilities[1])

        prediction_index = int(np.argmax(probabilities))
        prediction = (
            "Fraud"
            if prediction_index == 0
            else "Legitimate"
        )

        # -------------------------
        # SHAP
        # -------------------------
        shap_values = self._shap_explainer(
            encoded_input,
            max_evals=2 * len(self.feature_order) + 1,
        )

        shap_fraud = self._extract_fraud_values(shap_values)

        # -------------------------
        # LIME
        # -------------------------
        lime_result = self._lime_explainer.explain_instance(
            encoded_input[0],
            self._predict_proba_encoded,
            labels=(0,),
            num_samples=self.lime_samples,
        )

        lime_by_index = {
            int(index): float(weight)
            for index, weight in lime_result.as_map().get(0, [])
        }

        # -------------------------
        # Build feature explanations
        # -------------------------
        features = []

        for index, feature in enumerate(self.feature_order):
            features.append(
                {
                    "feature": feature,
                    "value": data[feature],
                    "shap": float(shap_fraud[index]),
                    "lime": float(lime_by_index.get(index, 0.0)),
                }
            )

        features.sort(
            key=lambda item: max(
                abs(item["shap"]),
                abs(item["lime"]),
            ),
            reverse=True,
        )

        # SHAP/LIME explanation lists
        shap_explanation = [
            {
                "feature": item["feature"],
                "value": item["value"],
                "shap_value": item["shap"],
            }
            for item in features
        ]

        lime_explanation = [
            {
                "feature": item["feature"],
                "value": item["value"],
                "lime_weight": item["lime"],
            }
            for item in features
        ]

        # -------------------------
        # Human-readable explanation
        # -------------------------
        human_readable = build_human_readable_explanation(
            prediction=prediction,
            fraud_probability=fraud_probability,
            legitimate_probability=legitimate_probability,
            features=data,
            shap=shap_explanation,
            lime=lime_explanation,
        )

        return {
            "prediction": prediction,
            "fraud_probability": fraud_probability,
            "legitimate_probability": legitimate_probability,
            "explanation_source": "tabtransformer_xai",

            "explanation": {
                "type": "tabtransformer_xai",

                "summary": human_readable["summary"],
                "confidence_text": human_readable["confidence_text"],
                "key_factors": human_readable["key_factors"],
                "interpretation_note": human_readable["interpretation_note"],

                "features": features,

                "shap": shap_explanation,
                "lime": lime_explanation,
            },
        }

    @staticmethod
    def _extract_fraud_values(shap_values: Any) -> np.ndarray:
        values = np.asarray(shap_values.values)

        # For the current binary probability wrapper, SHAP should return
        # [samples, features]. Keep this helper defensive across SHAP versions.
        if values.ndim == 3:
            # If an output dimension exists, class 0 is Fraud.
            if values.shape[-1] == 2:
                values = values[:, :, 0]
            elif values.shape[1] == 2:
                values = values[:, 0, :]

        return np.asarray(values[0], dtype=np.float64)
