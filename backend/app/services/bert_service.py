from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


class BERTService:
    MAX_LENGTH = 160

    def __init__(self):
        # Repository root:
        # E:\Projects\Attention_Pay
        #
        # This file is:
        # E:\Projects\Attention_Pay\backend\app\services\bert_service.py
        #
        # parents[3] -> repository root
        project_root = Path(__file__).resolve().parents[3]
        self.model_dir = project_root / "model"

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_dir)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            self.model_dir
        )

        self.model.eval()

    def predict(self, url: str) -> dict:
        inputs = self.tokenizer(
            url,
            padding="max_length",
            truncation=True,
            max_length=self.MAX_LENGTH,
            return_tensors="pt",
        )

        with torch.no_grad():
            outputs = self.model(**inputs)

        probabilities = torch.softmax(outputs.logits, dim=-1)[0]

        phishing_probability = probabilities[0].item()
        legitimate_probability = probabilities[1].item()

        prediction_id = torch.argmax(probabilities).item()

        prediction = self.model.config.id2label[prediction_id]

        return {
            "prediction": prediction,
            "confidence": probabilities[prediction_id].item(),
            "phishing_probability": phishing_probability,
            "legitimate_probability": legitimate_probability,
        }