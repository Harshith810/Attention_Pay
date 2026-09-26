from pathlib import Path
from typing import Any

import joblib
import torch
import pandas as pd

from backend.ml.tabtransformer.model import TabTransformer


class FraudDetectionService:
    """
    Service responsible for loading the trained TabTransformer
    and performing Layer 2 fraud detection.

    This service contains:
        - Model loading
        - Scaler loading
        - Categorical encoder loading
        - Feature configuration loading
        - Input preprocessing
        - Model inference
        - Fraud/Legitimate prediction
    """

    # ---------------------------------------------------------
    # MODEL CONFIGURATION
    # ---------------------------------------------------------

    LABEL_MAPPING = {
        0: "Fraud",
        1: "Legitimate",
    }

    # The threshold selected during model evaluation.
    DEFAULT_THRESHOLD = 0.332

    # ---------------------------------------------------------
    # INITIALIZATION
    # ---------------------------------------------------------

    def __init__(self):

        # -----------------------------------------------------
        # Determine project root
        #
        # This file:
        #
        # backend/app/services/fraud_detection.py
        #
        # parents[0] -> services
        # parents[1] -> app
        # parents[2] -> backend
        # parents[3] -> project root
        # -----------------------------------------------------

        project_root = Path(
            __file__
        ).resolve().parents[3]

        self.artifact_dir = (
            project_root
            / "backend"
            / "ml"
            / "tabtransformer"
            / "artifacts"
        )

        # -----------------------------------------------------
        # Artifact paths
        # -----------------------------------------------------

        self.model_path = (
            self.artifact_dir
            / "tabtransformer_model.pt"
        )

        self.scaler_path = (
            self.artifact_dir
            / "scaler.joblib"
        )

        self.encoder_path = (
            self.artifact_dir
            / "cat_encoders.joblib"
        )

        self.feature_config_path = (
            self.artifact_dir
            / "feature_config.joblib"
        )

        # -----------------------------------------------------
        # Device
        #
        # Backend inference normally runs on CPU.
        # If CUDA is available, PyTorch can use it.
        # -----------------------------------------------------

        self.device = torch.device(
            "cuda"
            if torch.cuda.is_available()
            else "cpu"
        )

        # -----------------------------------------------------
        # Load preprocessing artifacts
        # -----------------------------------------------------

        self.scaler = joblib.load(
            self.scaler_path
        )

        self.cat_encoders = joblib.load(
            self.encoder_path
        )

        self.feature_config = joblib.load(
            self.feature_config_path
        )

        # -----------------------------------------------------
        # Load model checkpoint
        # -----------------------------------------------------

        self.checkpoint = torch.load(
            self.model_path,
            map_location=self.device,
            weights_only=False,
        )

        # -----------------------------------------------------
        # Read model configuration from checkpoint
        # -----------------------------------------------------

        self.cat_cardinalities = (
            self.checkpoint["cat_cardinalities"]
        )

        self.num_numerical = (
            self.checkpoint["num_numerical"]
        )

        self.embed_dim = (
            self.checkpoint["embed_dim"]
        )

        self.n_heads = (
            self.checkpoint["n_heads"]
        )

        self.n_layers = (
            self.checkpoint["n_layers"]
        )

        self.num_classes = (
            self.checkpoint["num_classes"]
        )

        self.dropout = (
            self.checkpoint["dropout"]
        )

        # -----------------------------------------------------
        # Reconstruct the exact trained model architecture
        # -----------------------------------------------------

        self.model = TabTransformer(

            cat_cardinalities=self.cat_cardinalities,

            num_numerical=self.num_numerical,

            embed_dim=self.embed_dim,

            n_heads=self.n_heads,

            n_layers=self.n_layers,

            num_classes=self.num_classes,

            dropout=self.dropout,
        )

        # -----------------------------------------------------
        # Load trained weights
        # -----------------------------------------------------

        self.model.load_state_dict(
            self.checkpoint["model_state_dict"]
        )

        self.model.to(
            self.device
        )

        self.model.eval()

        # -----------------------------------------------------
        # Feature configuration
        # -----------------------------------------------------

        self.feature_order = (
            self.feature_config[
                "full_feature_order"
            ]
        )

        self.threshold = float(
            self.feature_config.get(
                "chosen_threshold",
                self.DEFAULT_THRESHOLD,
            )
        )

    # =========================================================
    # CATEGORY ENCODING
    # =========================================================

    def encode_category(
        self,
        column_name: str,
        value: str,
    ) -> int:
        """
        Convert a categorical value into the integer encoding
        expected by the trained TabTransformer.
        """

        if column_name not in self.cat_encoders:

            raise ValueError(
                f"No categorical encoder found "
                f"for '{column_name}'."
            )

        encoder = self.cat_encoders[
            column_name
        ]

        try:

            encoded = encoder.transform(
                [value]
            )[0]

        except Exception as error:

            raise ValueError(
                f"Invalid value '{value}' "
                f"for categorical feature "
                f"'{column_name}'. "
                f"Expected one of the categories "
                f"known by the trained encoder."
            ) from error

        return int(
            encoded
        )

    # =========================================================
    # INPUT PREPARATION
    # =========================================================

    def prepare_input(
        self,
        data: dict[str, Any],
    ) -> tuple[list[int], list[float]]:
        """
        Convert the canonical 11-feature transaction dictionary
        into categorical and numerical model inputs.

        IMPORTANT:
        The order must remain identical to the order used during
        model training.
        """

        # -----------------------------------------------------
        # Categorical features
        #
        # The trained model uses exactly three:
        #
        # 1. device_type
        # 2. browser_name
        # 3. operating_system
        # -----------------------------------------------------

        categorical = [

            self.encode_category(
                "device_type",
                data["device_type"],
            ),

            self.encode_category(
                "browser_name",
                data["browser_name"],
            ),

            self.encode_category(
                "operating_system",
                data["operating_system"],
            ),
        ]

        # -----------------------------------------------------
        # Numerical features
        #
        # IMPORTANT:
        # This order must match the training preprocessing.
        # -----------------------------------------------------

        numerical_features = [
        "known_device_flag",
        "device_changed_flag",
        "transactions_last_1min",
        "transactions_last_5min",
        "transactions_last_10min",
        "transaction_amount",
        "previous_transaction_amount",
        "session_risk_score",
        ]

        numerical = [
            data[feature]
            for feature in numerical_features
        ]

        # -----------------------------------------------------
        # Scale numerical features using the SAME scaler
        # used during training.
        # -----------------------------------------------------

        numerical_df = pd.DataFrame(
            [numerical],
            columns=numerical_features,
        )

        numerical_scaled = self.scaler.transform(
            numerical_df
        )[0]

        return (
            categorical,
            numerical_scaled.tolist(),
        )

    # =========================================================
    # PREDICTION
    # =========================================================

    def predict(
        self,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Run one transaction through the trained
        TabTransformer.

        Returns:
            Fraud probability
            Legitimate probability
            Prediction
            Threshold
        """

        # -----------------------------------------------------
        # Validate binary flags
        # -----------------------------------------------------

        if data["known_device_flag"] not in [0, 1]:

            raise ValueError(
                "known_device_flag must be 0 or 1."
            )

        if data["device_changed_flag"] not in [0, 1]:

            raise ValueError(
                "device_changed_flag must be 0 or 1."
            )

        # -----------------------------------------------------
        # Validate transaction velocity relationship
        #
        # 1 minute <= 5 minutes <= 10 minutes
        # -----------------------------------------------------

        if not (
            data["transactions_last_1min"]
            <= data["transactions_last_5min"]
            <= data["transactions_last_10min"]
        ):

            raise ValueError(
                "Invalid transaction velocity. "
                "Required relationship: "
                "transactions_last_1min <= "
                "transactions_last_5min <= "
                "transactions_last_10min."
            )

        # -----------------------------------------------------
        # Prepare model inputs
        # -----------------------------------------------------

        (
            categorical,
            numerical,
        ) = self.prepare_input(
            data
        )

        # -----------------------------------------------------
        # Convert to PyTorch tensors
        # -----------------------------------------------------

        categorical_tensor = torch.tensor(

            [categorical],

            dtype=torch.long,

            device=self.device,
        )

        numerical_tensor = torch.tensor(

            [numerical],

            dtype=torch.float32,

            device=self.device,
        )

        # -----------------------------------------------------
        # Model inference
        # -----------------------------------------------------

        with torch.no_grad():

            logits = self.model(

                categorical_tensor,

                numerical_tensor,
            )

        # -----------------------------------------------------
        # Convert logits to probabilities
        # -----------------------------------------------------

        probabilities = torch.softmax(
            logits,
            dim=1,
        )

        # -----------------------------------------------------
        # Project label mapping:
        #
        # 0 = Fraud
        # 1 = Legitimate
        # -----------------------------------------------------

        fraud_probability = probabilities[
            0,
            0,
        ].item()

        legitimate_probability = probabilities[
            0,
            1,
        ].item()

        # -----------------------------------------------------
        # Apply project threshold
        # -----------------------------------------------------

        prediction = (

            "Fraud"

            if fraud_probability >= self.threshold

            else "Legitimate"
        )

        # -----------------------------------------------------
        # Return prediction
        # -----------------------------------------------------

        return {

            "prediction": prediction,

            "fraud_probability": round(
                fraud_probability,
                6,
            ),

            "legitimate_probability": round(
                legitimate_probability,
                6,
            ),

            "threshold": self.threshold,

            "model": "TabTransformer",

            "label_mapping": {
                "0": "Fraud",
                "1": "Legitimate",
            },
        }

    # =========================================================
    # MODEL INFORMATION
    # =========================================================

    def get_model_info(
        self,
    ) -> dict[str, Any]:
        """
        Return information about the loaded model.
        Useful for health checks and debugging.
        """

        return {

            "model_loaded": True,

            "device": str(
                self.device
            ),

            "threshold": self.threshold,

            "feature_count": len(
                self.feature_order
            ),

            "features": self.feature_order,

            "categorical_features": [
                "device_type",
                "browser_name",
                "operating_system",
            ],

            "numerical_features": [
                "known_device_flag",
                "device_changed_flag",
                "transactions_last_1min",
                "transactions_last_5min",
                "transactions_last_10min",
                "transaction_amount",
                "previous_transaction_amount",
                "session_risk_score",
            ],

            "label_mapping": {
                "0": "Fraud",
                "1": "Legitimate",
            },
        }


# =============================================================
# SINGLE SERVICE INSTANCE
# =============================================================
#
# The model and preprocessing artifacts are loaded once when
# this module is imported instead of being loaded for every
# transaction request.
# =============================================================

fraud_detection_service = FraudDetectionService()