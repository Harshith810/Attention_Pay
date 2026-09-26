from typing import Any

import torch


class BERTExplainer:
    """
    Generates a URL-oriented explanation for the Stage 1 BERT model.

    The explanation uses the final transformer layer's CLS-to-token
    attention, averaged across attention heads.

    Attention should be interpreted as:
        "URL components the model focused on"

    It should NOT be interpreted as a guaranteed causal explanation.
    """

    MAX_LENGTH = 160
    TOP_TOKEN_COUNT = 8

    def __init__(self, tokenizer, model):
        self.tokenizer = tokenizer
        self.model = model

    def _is_special_token(self, token_id: int) -> bool:
        """Return True when the token is a special tokenizer token."""

        special_token_ids = set()

        for token_name in [
            "cls_token_id",
            "sep_token_id",
            "pad_token_id",
            "bos_token_id",
            "eos_token_id",
        ]:
            token_id_value = getattr(
                self.tokenizer,
                token_name,
                None,
            )

            if token_id_value is not None:
                special_token_ids.add(token_id_value)

        return token_id in special_token_ids

    def _merge_subword_tokens(
        self,
        token_data: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Merge WordPiece tokens such as:

            pay + ##pal -> paypal
            log + ##in  -> login

        The resulting token retains the highest importance score
        among its component tokens.
        """

        merged = []

        for item in token_data:
            token = item["token"]

            if token.startswith("##") and merged:
                previous = merged[-1]

                previous["token"] += token[2:]

                previous["importance"] = max(
                    previous["importance"],
                    item["importance"],
                )

                previous["positions"].append(
                    item["position"]
                )

            else:
                merged.append(
                    {
                        "token": token,
                        "importance": item["importance"],
                        "positions": [item["position"]],
                    }
                )

        return merged

    def _normalize_scores(
        self,
        token_data: list[dict[str, Any]],
    ) -> None:
        """
        Normalize scores relative to the highest attention value.

        This is only for visualization/ranking and does not mean
        that the score represents a probability or causal contribution.
        """

        if not token_data:
            return

        max_score = max(
            item["importance"]
            for item in token_data
        )

        if max_score <= 0:
            return

        for item in token_data:
            item["importance"] = round(
                item["importance"] / max_score,
                6,
            )

    def explain(self, url: str) -> dict[str, Any]:
        """
        Generate a URL explanation.

        Returns a JSON-serializable dictionary.
        """

        inputs = self.tokenizer(
            url,
            padding="max_length",
            truncation=True,
            max_length=self.MAX_LENGTH,
            return_tensors="pt",
        )

        device = next(
            self.model.parameters()
        ).device

        inputs = {
            key: value.to(device)
            for key, value in inputs.items()
        }

        with torch.no_grad():
            outputs = self.model(
                **inputs,
                output_attentions=True,
                return_dict=True,
            )

        attentions = outputs.attentions

        if not attentions:
            raise RuntimeError(
                "BERT model did not return attention weights. "
                "Ensure attn_implementation='eager' is used "
                "when loading the model."
            )

        # ---------------------------------------------------------
        # Last transformer layer
        # ---------------------------------------------------------

        last_layer_attention = attentions[-1]

        # Shape:
        # [batch, heads, sequence_length, sequence_length]
        #
        # Select:
        #   batch = 0
        #   all heads
        #   CLS token as source
        #   every token as destination
        cls_attention = last_layer_attention[
            0, :, 0, :
        ]

        # Average attention across heads.
        token_scores = cls_attention.mean(
            dim=0
        )

        token_scores = (
            token_scores
            .detach()
            .cpu()
            .tolist()
        )

        input_ids = (
            inputs["input_ids"][0]
            .detach()
            .cpu()
            .tolist()
        )

        attention_mask = (
            inputs["attention_mask"][0]
            .detach()
            .cpu()
            .tolist()
        )

        tokens = self.tokenizer.convert_ids_to_tokens(
            input_ids
        )

        # ---------------------------------------------------------
        # Build raw token data
        # ---------------------------------------------------------

        raw_tokens = []

        for index, (
            token,
            token_id,
            score,
            mask,
        ) in enumerate(
            zip(
                tokens,
                input_ids,
                token_scores,
                attention_mask,
            )
        ):

            # Ignore padding.
            if mask == 0:
                continue

            # Ignore CLS/SEP/etc.
            if self._is_special_token(token_id):
                continue

            raw_tokens.append(
                {
                    "token": token,
                    "importance": float(score),
                    "position": index,
                }
            )

        if not raw_tokens:
            return {
                "type": "bert_url_explanation",
                "summary": (
                    "The URL was classified as phishing, "
                    "but no usable token-level attention "
                    "information was available."
                ),
                "suspicious_tokens": [],
                "attention": [],
            }

        # ---------------------------------------------------------
        # Merge WordPiece tokens
        # ---------------------------------------------------------

        merged_tokens = self._merge_subword_tokens(
            raw_tokens
        )

        # Normalize for visualization.
        self._normalize_scores(
            merged_tokens
        )

        # ---------------------------------------------------------
        # Suspicious/model-focused components
        # ---------------------------------------------------------

        suspicious_tokens = sorted(
            merged_tokens,
            key=lambda item: item["importance"],
            reverse=True,
        )[: self.TOP_TOKEN_COUNT]

        suspicious_tokens = [
            {
                "token": item["token"],
                "importance": item["importance"],
                "positions": item["positions"],
            }
            for item in suspicious_tokens
        ]

        # ---------------------------------------------------------
        # Full attention sequence
        # ---------------------------------------------------------

        attention = [
            {
                "token": item["token"],
                "importance": item["importance"],
                "positions": item["positions"],
            }
            for item in merged_tokens
        ]

        return {
            "type": "bert_url_explanation",
            "summary": (
                "The URL was classified as phishing. "
                "The following URL components received "
                "relatively higher attention from the "
                "BERT model."
            ),
            "suspicious_tokens": suspicious_tokens,
            "attention": attention,
        }