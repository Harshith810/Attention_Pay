"""
url_detection_service.py
AttentionPay - Layer 1: Phishing URL Detection

Loads the fine-tuned BERT model and exposes predict_url().
This is the final function Person B (backend) will import and call.

Usage:
    from url_detection_service import predict_url
    result = predict_url("http://paypal-login-security.xyz")
"""

import re
import torch
from transformers import BertTokenizerFast, BertForSequenceClassification

# IMPORTANT: update this path to wherever the bert_phishing_model folder
# actually lives in the real project (e.g. ml/bert_phishing/bert_phishing_model)
MODEL_PATH = "./bert_phishing_model"

tokenizer = BertTokenizerFast.from_pretrained(MODEL_PATH)
model = BertForSequenceClassification.from_pretrained(
    MODEL_PATH,
    attn_implementation="eager",  # required so attention weights can be extracted for explainability
)
model.eval()

MAX_LENGTH = 128


def get_url_explanation(url, top_k=5):
    """
    Runs the URL through BERT and returns which meaningful tokens
    (words, not punctuation) the model paid the most attention to.
    """
    device = next(model.parameters()).device
    encoding = tokenizer(
        url,
        truncation=True,
        padding="max_length",
        max_length=MAX_LENGTH,
        return_tensors="pt",
    ).to(device)

    with torch.no_grad():
        outputs = model(**encoding, output_attentions=True)

    last_layer_attention = outputs.attentions[-1][0]
    avg_attention = last_layer_attention.mean(dim=0)
    cls_attention = avg_attention[0]

    tokens = tokenizer.convert_ids_to_tokens(encoding["input_ids"][0])

    token_scores = []
    for tok, score in zip(tokens, cls_attention.tolist()):
        if tok in ("[CLS]", "[SEP]", "[PAD]"):
            continue
        # Skip pure punctuation / separators / single non-letter characters
        clean = tok.replace("##", "")
        if not re.search(r"[a-zA-Z0-9]{2,}", clean):
            continue
        token_scores.append((tok, round(score, 4)))

    token_scores.sort(key=lambda x: x[1], reverse=True)
    top_tokens = token_scores[:top_k]

    return {
        "top_suspicious_tokens": [t for t, s in top_tokens],
        "token_attention_scores": top_tokens,
    }


def build_explanation_text(prediction, top_tokens):
    """
    Turns the raw top tokens into a plain-English explanation.
    """
    clean_tokens = [t.replace("##", "") for t in top_tokens]

    if prediction == "phishing":
        summary = "This URL was flagged as phishing based on suspicious patterns in its structure."
        reasons = [f"Suspicious element detected: '{t}'" for t in clean_tokens]
    else:
        summary = "This URL appears legitimate based on its structure and domain pattern."
        reasons = [f"Recognized normal element: '{t}'" for t in clean_tokens]

    return summary, reasons


def predict_url(url):
    """
    Final function for Layer 1 (Phishing URL Detection).

    Input:  a URL string
    Output: a dictionary with prediction, confidence, probabilities,
            and a full explanation (summary + reasons + highlighted tokens)
    """
    device = next(model.parameters()).device
    encoding = tokenizer(
        url,
        truncation=True,
        padding="max_length",
        max_length=MAX_LENGTH,
        return_tensors="pt",
    ).to(device)

    with torch.no_grad():
        outputs = model(**encoding)
        probs = torch.softmax(outputs.logits, dim=-1)[0]

    prediction = "phishing" if probs[0] > probs[1] else "legitimate"
    confidence = float(max(probs))

    explanation_data = get_url_explanation(url)
    summary, reasons = build_explanation_text(prediction, explanation_data["top_suspicious_tokens"])

    return {
        "url": url,
        "prediction": prediction,
        "confidence": round(confidence, 4),
        "phishing_probability": round(float(probs[0]), 4),
        "legitimate_probability": round(float(probs[1]), 4),
        "explanation": {
            "summary": summary,
            "reasons": reasons,
            "highlighted_tokens": explanation_data["token_attention_scores"],
        },
        "explanation_source": "bert_xai",
    }
