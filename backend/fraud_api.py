"""Standalone FastAPI service for the trained AttentionPay TabTransformer.

Run from the backend folder:
    python -m uvicorn fraud_api:app --reload --port 8000

Set TABTRANSFORMER_ARTIFACTS_DIR only when the artifacts live elsewhere.
"""

from __future__ import annotations

import os
import warnings
from pathlib import Path
from typing import Literal

import joblib
import numpy as np
import torch
import torch.nn as nn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, model_validator
from sklearn.exceptions import InconsistentVersionWarning


DEFAULT_ARTIFACTS_DIR = (
    Path(__file__).resolve().parents[3]
    / "tabtransformer"
    / "tabtransformer_artifacts_hershit"
)
ARTIFACTS_DIR = Path(
    os.getenv("TABTRANSFORMER_ARTIFACTS_DIR", str(DEFAULT_ARTIFACTS_DIR))
).resolve()
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class FraudPredictionRequest(BaseModel):
    known_device_flag: int = Field(ge=0, le=1)
    device_changed_flag: int = Field(ge=0, le=1)
    device_type: Literal["desktop", "mobile", "tablet"]
    browser_name: Literal["chrome", "edge", "firefox", "safari"]
    operating_system: Literal["android", "ios", "linux", "macos", "windows"]
    transactions_last_1min: int = Field(ge=0)
    transactions_last_5min: int = Field(ge=0)
    transactions_last_10min: int = Field(ge=0)
    transaction_amount: float = Field(ge=0)
    previous_transaction_amount: float = Field(ge=0)
    session_risk_score: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def validate_velocity_windows(self) -> "FraudPredictionRequest":
        if not (
            self.transactions_last_1min
            <= self.transactions_last_5min
            <= self.transactions_last_10min
        ):
            raise ValueError(
                "transactions_last_1min must be <= transactions_last_5min "
                "and <= transactions_last_10min"
            )
        return self


class FraudPredictionResponse(BaseModel):
    prediction: Literal["fraud", "legitimate"]
    fraud_probability: float
    legitimate_probability: float
    threshold_used: float


class TabTransformer(nn.Module):
    def __init__(
        self,
        cat_cardinalities: list[int],
        num_numerical: int,
        embed_dim: int = 32,
        n_heads: int = 4,
        n_layers: int = 2,
        num_classes: int = 2,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.cat_embeddings = nn.ModuleList(
            [nn.Embedding(cardinality, embed_dim) for cardinality in cat_cardinalities]
        )
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embed_dim,
            nhead=n_heads,
            dim_feedforward=embed_dim * 4,
            dropout=dropout,
            batch_first=True,
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=n_layers)
        self.num_norm = nn.LayerNorm(num_numerical)
        combined_dim = (embed_dim * len(cat_cardinalities)) + num_numerical
        self.mlp = nn.Sequential(
            nn.Linear(combined_dim, 128), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(128, 64), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(64, num_classes),
        )

    def forward(self, categorical: torch.Tensor, numerical: torch.Tensor) -> torch.Tensor:
        embedded = [embedding(categorical[:, index]) for index, embedding in enumerate(self.cat_embeddings)]
        categorical_features = self.transformer(torch.stack(embedded, dim=1)).flatten(start_dim=1)
        combined = torch.cat([categorical_features, self.num_norm(numerical)], dim=1)
        return self.mlp(combined)


class FraudModelService:
    def __init__(self, artifacts_dir: Path) -> None:
        required_files = (
            "tabtransformer_model.pt", "scaler.joblib", "cat_encoders.joblib", "feature_config.joblib"
        )
        missing = [name for name in required_files if not (artifacts_dir / name).is_file()]
        if missing:
            raise RuntimeError(f"Missing model artifacts in {artifacts_dir}: {', '.join(missing)}")

        checkpoint = torch.load(artifacts_dir / "tabtransformer_model.pt", map_location=DEVICE, weights_only=False)
        # The artifacts contain only StandardScaler and LabelEncoder instances.
        # They are compatible with the supported current scikit-learn runtime,
        # though joblib emits a warning because the training environment used 1.6.1.
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=InconsistentVersionWarning)
            self.scaler = joblib.load(artifacts_dir / "scaler.joblib")
            self.cat_encoders = joblib.load(artifacts_dir / "cat_encoders.joblib")
            feature_config = joblib.load(artifacts_dir / "feature_config.joblib")
        self.categorical_columns = feature_config["categorical_cols"]
        self.numerical_columns = feature_config["numerical_cols"]
        self.threshold = float(feature_config["chosen_threshold"])
        self.model = TabTransformer(
            cat_cardinalities=checkpoint["cat_cardinalities"],
            num_numerical=checkpoint["num_numerical"],
            embed_dim=checkpoint["embed_dim"],
            n_heads=checkpoint["n_heads"],
            n_layers=checkpoint["n_layers"],
            num_classes=checkpoint["num_classes"],
            dropout=checkpoint["dropout"],
        ).to(DEVICE)
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.model.eval()

    def predict(self, payload: FraudPredictionRequest) -> dict[str, float | str]:
        values = payload.model_dump()
        categorical_values = [
            self.cat_encoders[column].transform([values[column]])[0]
            for column in self.categorical_columns
        ]
        numerical_values = np.asarray(
            [[values[column] for column in self.numerical_columns]], dtype=np.float32
        )
        scaled_numerical = self.scaler.transform(numerical_values)
        categorical = torch.tensor([categorical_values], dtype=torch.long, device=DEVICE)
        numerical = torch.tensor(scaled_numerical, dtype=torch.float32, device=DEVICE)

        with torch.inference_mode():
            probabilities = torch.softmax(self.model(categorical, numerical), dim=1)[0]
        fraud_probability = float(probabilities[0].item())
        legitimate_probability = float(probabilities[1].item())
        return {
            "prediction": "fraud" if fraud_probability >= self.threshold else "legitimate",
            "fraud_probability": round(fraud_probability, 4),
            "legitimate_probability": round(legitimate_probability, 4),
            "threshold_used": self.threshold,
        }


app = FastAPI(title="AttentionPay Fraud Prediction API", version="1.0.0")
model_service: FraudModelService | None = None
model_load_error: str | None = None


@app.on_event("startup")
def load_model() -> None:
    global model_service, model_load_error
    try:
        model_service = FraudModelService(ARTIFACTS_DIR)
        model_load_error = None
    except Exception as error:
        model_service = None
        model_load_error = str(error)


@app.get("/health")
def health() -> dict[str, str]:
    if model_load_error:
        raise HTTPException(status_code=503, detail=model_load_error)
    return {"status": "ok", "artifacts_dir": str(ARTIFACTS_DIR), "device": str(DEVICE)}


@app.post("/api/v1/fraud/predict", response_model=FraudPredictionResponse)
def predict_fraud(payload: FraudPredictionRequest) -> dict[str, float | str]:
    if model_service is None:
        raise HTTPException(status_code=503, detail=model_load_error or "Model is not loaded")
    return model_service.predict(payload)
