import os
import json
import numpy as np
import pandas as pd
import torch

from tqdm import tqdm
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    classification_report,
    confusion_matrix,
)


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_DIR = "model"
TEST_FILE = "dataset/test.csv"
RESULTS_DIR = "results"

MAX_LENGTH = 160
BATCH_SIZE = 32

# Our project label mapping
PHISHING = 0
LEGITIMATE = 1


# ============================================================
# SETUP
# ============================================================

os.makedirs(RESULTS_DIR, exist_ok=True)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print("=" * 60)
print("AttentionPay - Stage 1 BERT Evaluation")
print("=" * 60)

print(f"Device: {device}")

if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")

print(f"Model directory: {MODEL_DIR}")
print(f"Test dataset: {TEST_FILE}")
print(f"Maximum sequence length: {MAX_LENGTH}")
print(f"Batch size: {BATCH_SIZE}")


# ============================================================
# LOAD TEST DATA
# ============================================================

print("\nLoading test dataset...")

test_df = pd.read_csv(TEST_FILE)

print(f"Test samples: {len(test_df):,}")
print(f"Columns: {list(test_df.columns)}")

# Validate required columns
required_columns = {"URL", "label"}

if not required_columns.issubset(test_df.columns):
    raise ValueError(
        f"Test dataset must contain columns: {required_columns}"
    )

# Check missing values
print("\nMissing values:")
print(test_df[["URL", "label"]].isnull().sum())

# Remove rows with missing values just in case
if test_df[["URL", "label"]].isnull().any().any():
    raise ValueError("Missing values found in URL or label column.")

# Verify labels
unique_labels = sorted(test_df["label"].unique())

print("\nUnique labels:", unique_labels)

if unique_labels != [0, 1]:
    raise ValueError(
        f"Expected labels [0, 1], but found {unique_labels}"
    )

print("\nTest label distribution:")
print(test_df["label"].value_counts().sort_index())


# ============================================================
# LOAD TOKENIZER
# ============================================================

print("\nLoading tokenizer...")

tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)

print("Tokenizer loaded successfully!")
print("Vocabulary size:", tokenizer.vocab_size)


# ============================================================
# LOAD TRAINED MODEL
# ============================================================

print("\nLoading trained BERT model...")

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_DIR
)

model.to(device)
model.eval()

print("Model loaded successfully!")
print("Model type:", type(model).__name__)
print("Number of labels:", model.config.num_labels)
print("Label mapping:", model.config.id2label)


# ============================================================
# PREPARE TEST DATA
# ============================================================

urls = test_df["URL"].astype(str).tolist()
true_labels = test_df["label"].to_numpy()

predictions = []
probabilities = []


# ============================================================
# RUN INFERENCE
# ============================================================

print("\nRunning inference...")
print(f"Total URLs: {len(urls):,}")

with torch.no_grad():

    for start in tqdm(
        range(0, len(urls), BATCH_SIZE),
        desc="Evaluating",
    ):

        batch_urls = urls[start:start + BATCH_SIZE]

        encoded = tokenizer(
            batch_urls,
            padding="max_length",
            truncation=True,
            max_length=MAX_LENGTH,
            return_tensors="pt",
        )

        encoded = {
            key: value.to(device)
            for key, value in encoded.items()
        }

        outputs = model(**encoded)

        logits = outputs.logits

        probs = torch.softmax(logits, dim=-1)

        batch_predictions = torch.argmax(
            probs,
            dim=-1
        )

        predictions.extend(
            batch_predictions.cpu().numpy()
        )

        probabilities.extend(
            probs.cpu().numpy()
        )


predictions = np.array(predictions)
probabilities = np.array(probabilities)


# ============================================================
# CALCULATE METRICS
# ============================================================

print("\nCalculating metrics...")

accuracy = accuracy_score(
    true_labels,
    predictions
)

precision = precision_score(
    true_labels,
    predictions,
    pos_label=LEGITIMATE,
    zero_division=0
)

recall = recall_score(
    true_labels,
    predictions,
    pos_label=LEGITIMATE,
    zero_division=0
)

f1 = f1_score(
    true_labels,
    predictions,
    pos_label=LEGITIMATE,
    zero_division=0
)

# Probability of class 1 (LEGITIMATE)
legitimate_probabilities = probabilities[:, LEGITIMATE]

roc_auc = roc_auc_score(
    true_labels,
    legitimate_probabilities
)


# ============================================================
# CLASSIFICATION REPORT
# ============================================================

report = classification_report(
    true_labels,
    predictions,
    target_names=[
        "PHISHING",
        "LEGITIMATE"
    ],
    digits=6,
    zero_division=0
)


# ============================================================
# CONFUSION MATRIX
# ============================================================

cm = confusion_matrix(
    true_labels,
    predictions,
    labels=[
        PHISHING,
        LEGITIMATE
    ]
)


# ============================================================
# DISPLAY RESULTS
# ============================================================

print("\n")
print("=" * 60)
print("FINAL TEST RESULTS")
print("=" * 60)

print(f"Accuracy : {accuracy:.6f} ({accuracy * 100:.4f}%)")
print(f"Precision: {precision:.6f} ({precision * 100:.4f}%)")
print(f"Recall   : {recall:.6f} ({recall * 100:.4f}%)")
print(f"F1 Score : {f1:.6f} ({f1 * 100:.4f}%)")
print(f"ROC AUC  : {roc_auc:.6f}")

print("\nClassification Report:")
print(report)

print("Confusion Matrix:")
print(cm)

print("\nMatrix format:")
print("                 Predicted")
print("                 Phishing  Legitimate")
print(
    f"Actual Phishing    {cm[0,0]:8d}  {cm[0,1]:10d}"
)
print(
    f"Actual Legitimate  {cm[1,0]:8d}  {cm[1,1]:10d}"
)


# ============================================================
# SAVE RESULTS
# ============================================================

metrics = {
    "model": "bert-base-uncased",
    "max_length": MAX_LENGTH,
    "test_samples": int(len(test_df)),
    "accuracy": float(accuracy),
    "precision_legitimate": float(precision),
    "recall_legitimate": float(recall),
    "f1_legitimate": float(f1),
    "roc_auc": float(roc_auc),
    "confusion_matrix": cm.tolist(),
}

metrics_file = os.path.join(
    RESULTS_DIR,
    "test_metrics.json"
)

with open(metrics_file, "w") as f:
    json.dump(metrics, f, indent=4)


report_file = os.path.join(
    RESULTS_DIR,
    "classification_report.txt"
)

with open(report_file, "w") as f:
    f.write(report)


# Save individual predictions
predictions_df = test_df.copy()

predictions_df["predicted_label"] = predictions
predictions_df["phishing_probability"] = probabilities[:, PHISHING]
predictions_df["legitimate_probability"] = probabilities[:, LEGITIMATE]

predictions_file = os.path.join(
    RESULTS_DIR,
    "test_predictions.csv"
)

predictions_df.to_csv(
    predictions_file,
    index=False
)


print("\nResults saved successfully!")

print(f"Metrics:       {metrics_file}")
print(f"Report:        {report_file}")
print(f"Predictions:   {predictions_file}")

print("\nEvaluation completed successfully! 🎯")