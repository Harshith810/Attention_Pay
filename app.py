# ============================================================
# AttentionPay - TabTransformer Testing API
# ============================================================

import os

# Windows OpenMP workaround
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"

import torch
import torch.nn as nn
import joblib

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Literal


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ARTIFACT_DIR = os.path.join(
    BASE_DIR,
    "tabtransformer_artifacts"
)

MODEL_PATH = os.path.join(
    ARTIFACT_DIR,
    "tabtransformer_model.pt"
)

SCALER_PATH = os.path.join(
    ARTIFACT_DIR,
    "scaler.joblib"
)

ENCODER_PATH = os.path.join(
    ARTIFACT_DIR,
    "cat_encoders.joblib"
)

FEATURE_CONFIG_PATH = os.path.join(
    ARTIFACT_DIR,
    "feature_config.joblib"
)


# ============================================================
# DEVICE
# ============================================================

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="AttentionPay TabTransformer Testing API",
    version="1.0"
)


# ============================================================
# LOAD ARTIFACTS
# ============================================================

print()
print("==========================================")
print("AttentionPay TabTransformer API")
print("==========================================")
print("Model          :", MODEL_PATH)
print("Scaler         :", SCALER_PATH)
print("Encoders       :", ENCODER_PATH)
print("Feature config :", FEATURE_CONFIG_PATH)
print("==========================================")
print()

print("Using device:", DEVICE)


scaler = joblib.load(
    SCALER_PATH
)

cat_encoders = joblib.load(
    ENCODER_PATH
)

feature_config = joblib.load(
    FEATURE_CONFIG_PATH
)

print("✓ scaler.joblib loaded")
print("✓ cat_encoders.joblib loaded")
print("✓ feature_config.joblib loaded")

print()
print("Feature configuration:")
print(feature_config)

print()
print("Categorical encoders:")
print(cat_encoders)


# ============================================================
# LOAD CHECKPOINT
# ============================================================

print()
print("Loading checkpoint...")

checkpoint = torch.load(
    MODEL_PATH,
    map_location=DEVICE,
    weights_only=False
)

print("✓ Checkpoint loaded")

print()
print("Checkpoint keys:")
print(list(checkpoint.keys()))


# ============================================================
# READ MODEL CONFIGURATION
# ============================================================

cat_cardinalities = checkpoint[
    "cat_cardinalities"
]

num_numerical = checkpoint[
    "num_numerical"
]

embed_dim = checkpoint[
    "embed_dim"
]

n_heads = checkpoint[
    "n_heads"
]

n_layers = checkpoint[
    "n_layers"
]

num_classes = checkpoint[
    "num_classes"
]

dropout = checkpoint[
    "dropout"
]


print()
print("==========================================")
print("MODEL CONFIGURATION")
print("==========================================")
print("Categorical cardinalities :", cat_cardinalities)
print("Numerical features        :", num_numerical)
print("Embedding dimension       :", embed_dim)
print("Attention heads           :", n_heads)
print("Transformer layers        :", n_layers)
print("Number of classes         :", num_classes)
print("Dropout                   :", dropout)
print("==========================================")


# ============================================================
# TABTRANSFORMER ARCHITECTURE
# ============================================================

class TabTransformer(nn.Module):

    def __init__(
        self,
        cat_cardinalities,
        num_numerical,
        embed_dim,
        n_heads,
        n_layers,
        num_classes,
        dropout
    ):

        super().__init__()


        # ----------------------------------------------------
        # Categorical embeddings
        # ----------------------------------------------------

        self.cat_embeddings = nn.ModuleList([

            nn.Embedding(
                cardinality,
                embed_dim
            )

            for cardinality
            in cat_cardinalities

        ])


        # ----------------------------------------------------
        # Transformer encoder
        # ----------------------------------------------------

        encoder_layer = nn.TransformerEncoderLayer(

            d_model=embed_dim,

            nhead=n_heads,

            dim_feedforward=embed_dim * 4,

            dropout=dropout,

            activation="gelu",

            batch_first=True,

            norm_first=False

        )


        self.transformer = nn.TransformerEncoder(

            encoder_layer,

            num_layers=n_layers

        )


        # ----------------------------------------------------
        # Numerical feature normalization
        # ----------------------------------------------------

        self.num_norm = nn.LayerNorm(
            num_numerical
        )


        # ----------------------------------------------------
        # Final classifier
        #
        # Transformer output:
        #   3 categorical embeddings
        #
        # Flattened:
        #   3 * embed_dim
        #
        # Numerical:
        #   8
        # ----------------------------------------------------

        # ----------------------------------------------------
        # MLP classifier
        # ----------------------------------------------------

        input_dim = (
            len(cat_cardinalities) * embed_dim
            + num_numerical
        )

        self.mlp = nn.Sequential(

            nn.Linear(
                input_dim,
                128
            ),

            nn.ReLU(),

            nn.Dropout(dropout),

            nn.Linear(
                128,
                64
            ),

            nn.ReLU(),

            nn.Dropout(dropout),

            nn.Linear(
                64,
                num_classes
            )

        )


    def forward(
        self,
        categorical,
        numerical
    ):

        # ----------------------------------------------------
        # Embed categorical features
        # ----------------------------------------------------

        embedded = []

        for i, embedding in enumerate(
            self.cat_embeddings
        ):

            embedded.append(

                embedding(
                    categorical[:, i]
                )

            )


        # ----------------------------------------------------
        # [batch, number_of_categories, embed_dim]
        # ----------------------------------------------------

        x = torch.stack(
            embedded,
            dim=1
        )


        # ----------------------------------------------------
        # Transformer
        # ----------------------------------------------------

        x = self.transformer(
            x
        )


        # ----------------------------------------------------
        # Flatten categorical representation
        # ----------------------------------------------------

        x = x.reshape(
            x.size(0),
            -1
        )


        # ----------------------------------------------------
        # Normalize numerical features
        # ----------------------------------------------------

        numerical = self.num_norm(
            numerical
        )


        # ----------------------------------------------------
        # Combine
        # ----------------------------------------------------

        combined = torch.cat(
            [
                x,
                numerical
            ],
            dim=1
        )


        # ----------------------------------------------------
        # Classification
        # ----------------------------------------------------

        return self.mlp(
            combined
        )


# ============================================================
# CREATE MODEL
# ============================================================

model = TabTransformer(

    cat_cardinalities=cat_cardinalities,

    num_numerical=num_numerical,

    embed_dim=embed_dim,

    n_heads=n_heads,

    n_layers=n_layers,

    num_classes=num_classes,

    dropout=dropout

)


# ============================================================
# LOAD TRAINED WEIGHTS
# ============================================================

try:

    model.load_state_dict(
        checkpoint["model_state_dict"]
    )

except RuntimeError as e:

    print()
    print("MODEL STATE DICT ERROR")
    print("======================")
    print(e)

    raise


model.to(
    DEVICE
)

model.eval()


print()
print("✓ TabTransformer model reconstructed")
print("✓ Model weights loaded successfully")
print("✓ Model switched to evaluation mode")


# ============================================================
# MODEL CONTRACT
# ============================================================

THRESHOLD = float(
    feature_config.get(
        "chosen_threshold",
        0.332
    )
)


FEATURE_ORDER = feature_config[
    "full_feature_order"
]


print()
print("==========================================")
print("INFERENCE CONTRACT")
print("==========================================")
print("Features :", FEATURE_ORDER)
print("Threshold:", THRESHOLD)
print("==========================================")


# ============================================================
# REQUEST MODEL
# ============================================================

class TransactionInput(BaseModel):

    known_device_flag: int

    device_changed_flag: int

    device_type: Literal[
        "desktop",
        "mobile",
        "tablet"
    ]

    browser_name: Literal[
        "chrome",
        "firefox",
        "edge",
        "safari"
    ]

    operating_system: Literal[
        "android",
        "ios",
        "windows",
        "macos",
        "linux"
    ]

    transactions_last_1min: int

    transactions_last_5min: int

    transactions_last_10min: int

    transaction_amount: float

    previous_transaction_amount: float

    session_risk_score: float


# ============================================================
# CATEGORY ENCODING
# ============================================================

def encode_category(
    column_name,
    value
):

    encoder = cat_encoders[
        column_name
    ]

    try:

        encoded = encoder.transform(
            [value]
        )[0]

    except Exception as e:

        raise ValueError(
            f"Invalid {column_name} value "
            f"'{value}'. "
            f"Encoder error: {e}"
        )

    return int(
        encoded
    )


# ============================================================
# PREPARE MODEL INPUT
# ============================================================

def prepare_input(
    data
):

    # --------------------------------------------------------
    # Categorical features
    # --------------------------------------------------------

    categorical = [

        encode_category(
            "device_type",
            data.device_type
        ),

        encode_category(
            "browser_name",
            data.browser_name
        ),

        encode_category(
            "operating_system",
            data.operating_system
        )

    ]


    # --------------------------------------------------------
    # Numerical features
    #
    # IMPORTANT:
    # Order MUST match feature_config.joblib
    # --------------------------------------------------------

    numerical = [

        data.known_device_flag,

        data.device_changed_flag,

        data.transactions_last_1min,

        data.transactions_last_5min,

        data.transactions_last_10min,

        data.transaction_amount,

        data.previous_transaction_amount,

        data.session_risk_score

    ]


    # --------------------------------------------------------
    # Training scaler
    # --------------------------------------------------------

    numerical_scaled = scaler.transform(
        [numerical]
    )[0]


    return (
        categorical,
        numerical_scaled
    )


# ============================================================
# PREDICTION
# ============================================================

def predict_model(
    categorical,
    numerical
):

    categorical_tensor = torch.tensor(

        [categorical],

        dtype=torch.long,

        device=DEVICE

    )


    numerical_tensor = torch.tensor(

        [numerical],

        dtype=torch.float32,

        device=DEVICE

    )


    with torch.no_grad():

        logits = model(

            categorical_tensor,

            numerical_tensor

        )


    # --------------------------------------------------------
    # IMPORTANT:
    #
    # Project mapping:
    #
    # 0 = Fraud
    # 1 = Legitimate
    #
    # Therefore softmax index 0 = Fraud probability.
    # --------------------------------------------------------

    probabilities = torch.softmax(
        logits,
        dim=1
    )


    fraud_probability = probabilities[
        0,
        0
    ].item()


    legitimate_probability = probabilities[
        0,
        1
    ].item()


    return (
        fraud_probability,
        legitimate_probability
    )


# ============================================================
# HEALTH
# ============================================================

@app.get(
    "/health"
)
def health():

    return {

        "status": "ok",

        "model_loaded": True,

        "device": str(
            DEVICE
        ),

        "threshold": THRESHOLD,

        "feature_count": len(
            FEATURE_ORDER
        ),

        "features": FEATURE_ORDER,

        "label_mapping": {
            "0": "Fraud",
            "1": "Legitimate"
        }

    }


# ============================================================
# PREDICT ENDPOINT
# ============================================================

@app.post(
    "/predict"
)
def predict(
    data: TransactionInput
):

    try:

        # ----------------------------------------------------
        # Validate binary flags
        # ----------------------------------------------------

        if data.known_device_flag not in [0, 1]:

            raise HTTPException(

                status_code=400,

                detail="known_device_flag must be 0 or 1"

            )


        if data.device_changed_flag not in [0, 1]:

            raise HTTPException(

                status_code=400,

                detail="device_changed_flag must be 0 or 1"

            )


        # ----------------------------------------------------
        # Validate velocity relationship
        # ----------------------------------------------------

        if not (

            data.transactions_last_1min
            <=
            data.transactions_last_5min
            <=
            data.transactions_last_10min

        ):

            raise HTTPException(

                status_code=400,

                detail=(
                    "Invalid transaction velocity. "
                    "Required relationship: "
                    "transactions_last_1min <= "
                    "transactions_last_5min <= "
                    "transactions_last_10min"
                )

            )


        # ----------------------------------------------------
        # Prepare
        # ----------------------------------------------------

        categorical, numerical = prepare_input(
            data
        )


        # ----------------------------------------------------
        # Predict
        # ----------------------------------------------------

        (
            fraud_probability,
            legitimate_probability
        ) = predict_model(

            categorical,
            numerical

        )


        # ----------------------------------------------------
        # Apply project threshold
        # ----------------------------------------------------

        prediction = (

            "Fraud"

            if fraud_probability >= THRESHOLD

            else "Legitimate"

        )


        # ----------------------------------------------------
        # Return
        # ----------------------------------------------------

        return {

            "prediction": prediction,

            "fraud_probability": round(
                fraud_probability,
                6
            ),

            "legitimate_probability": round(
                legitimate_probability,
                6
            ),

            "threshold": THRESHOLD,

            "model": "Harshith TabTransformer",

            "label_mapping": {

                "0": "Fraud",

                "1": "Legitimate"

            },

            "input": data.model_dump(),

            "encoded_categorical": categorical,

            "scaled_numerical": [

                round(
                    float(x),
                    6
                )

                for x in numerical

            ]

        }


    except HTTPException:

        raise


    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=str(e)

        )


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {

        "message":
            "AttentionPay TabTransformer API",

        "endpoint":
            "/predict",

        "health":
            "/health",

        "feature_count":
            11,

        "threshold":
            THRESHOLD

    }

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8000,
        reload=False
    )