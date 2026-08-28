import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_DIR = "model"
MAX_LENGTH = 160

PHISHING = 0
LEGITIMATE = 1


# ============================================================
# DEVICE
# ============================================================

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("=" * 60)
print("AttentionPay - Stage 1 BERT URL Prediction")
print("=" * 60)

print("Device:", device)


# ============================================================
# LOAD TOKENIZER
# ============================================================

print("\nLoading tokenizer...")

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_DIR
)

print("Tokenizer loaded successfully!")


# ============================================================
# LOAD MODEL
# ============================================================

print("\nLoading model...")

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_DIR
)

model.to(device)
model.eval()

print("Model loaded successfully!")
print("Label mapping:", model.config.id2label)


# ============================================================
# PREDICTION FUNCTION
# ============================================================

def predict_url(url):

    encoded = tokenizer(
        url,
        padding="max_length",
        truncation=True,
        max_length=MAX_LENGTH,
        return_tensors="pt"
    )

    encoded = {
        key: value.to(device)
        for key, value in encoded.items()
    }

    with torch.no_grad():

        outputs = model(**encoded)

        probabilities = torch.softmax(
            outputs.logits,
            dim=-1
        )[0]

        prediction = torch.argmax(
            probabilities
        ).item()

    phishing_probability = probabilities[
        PHISHING
    ].item()

    legitimate_probability = probabilities[
        LEGITIMATE
    ].item()

    if prediction == PHISHING:
        result = "PHISHING"
        confidence = phishing_probability
    else:
        result = "LEGITIMATE"
        confidence = legitimate_probability

    return (
        result,
        confidence,
        phishing_probability,
        legitimate_probability
    )


# ============================================================
# INTERACTIVE LOOP
# ============================================================

print("\nModel is ready!")
print("Enter a URL to test.")
print("Type 'exit' to quit.")

while True:

    print("\n" + "-" * 60)

    url = input("URL: ").strip()

    if url.lower() == "exit":
        print("\nExiting...")
        break

    if not url:
        print("Please enter a URL.")
        continue

    result, confidence, phishing_prob, legitimate_prob = (
        predict_url(url)
    )

    print("\nPrediction")
    print("=" * 60)

    print("URL:", url)
    print("Result:", result)
    print(f"Confidence: {confidence * 100:.2f}%")

    print(
        f"Phishing probability: "
        f"{phishing_prob * 100:.2f}%"
    )

    print(
        f"Legitimate probability: "
        f"{legitimate_prob * 100:.2f}%"
    )