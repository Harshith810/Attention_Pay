from typing import Any


FEATURE_DESCRIPTIONS = {
    "transaction_amount": "the current transaction amount",
    "previous_transaction_amount": "the previous transaction amount",
    "session_risk_score": "the session risk score",
    "transactions_last_1min": "the number of transactions in the last minute",
    "transactions_last_5min": "the number of transactions in the last 5 minutes",
    "transactions_last_10min": "the number of transactions in the last 10 minutes",
    "known_device_flag": "whether the device is known",
    "device_changed_flag": "whether the device has changed",
    "device_type": "the device type",
    "browser_name": "the browser",
    "operating_system": "the operating system",
}


FEATURE_VALUE_DESCRIPTIONS = {
    "known_device_flag": {
        0: "an unknown device",
        1: "a known device",
    },
    "device_changed_flag": {
        0: "the same device as before",
        1: "a changed device",
    },
}


def _feature_name(feature: str) -> str:
    return FEATURE_DESCRIPTIONS.get(
        feature,
        feature.replace("_", " "),
    )


def _format_value(feature: str, value: Any) -> str:
    if feature in FEATURE_VALUE_DESCRIPTIONS:
        try:
            return FEATURE_VALUE_DESCRIPTIONS[feature][int(value)]
        except (KeyError, TypeError, ValueError):
            pass

    if isinstance(value, float):
        return f"{value:.2f}"

    return str(value)


def _extract_contribution(item: dict[str, Any]) -> float:
    """
    Support the common contribution keys produced by the
    SHAP/LIME explanation layer.
    """

    for key in (
        "contribution",
        "shap_value",
        "value",
        "importance",
        "weight",
    ):
        value = item.get(key)

        if isinstance(value, (int, float)):
            return float(value)

    return 0.0


def _extract_feature(item: dict[str, Any]) -> str | None:
    for key in (
        "feature",
        "feature_name",
        "name",
    ):
        value = item.get(key)

        if value is not None:
            return str(value)

    return None


def build_human_readable_explanation(
    *,
    prediction: str,
    fraud_probability: float,
    legitimate_probability: float,
    features: dict[str, Any],
    shap: list[dict[str, Any]],
    lime: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Convert SHAP/LIME feature contributions into a deterministic,
    human-readable explanation.

    This does NOT replace SHAP or LIME.

    The wording describes model contribution rather than claiming
    that a feature is a proven causal reason for the decision.
    """

    normalized_prediction = prediction.lower()

    # ---------------------------------------------------------
    # Normalize SHAP contributions
    # ---------------------------------------------------------

    shap_items = []

    for item in shap:
        feature = _extract_feature(item)

        if not feature:
            continue

        contribution = _extract_contribution(item)

        shap_items.append(
            {
                "feature": feature,
                "contribution": contribution,
                "absolute_contribution": abs(contribution),
            }
        )

    # ---------------------------------------------------------
    # Sort by contribution magnitude
    # ---------------------------------------------------------

    shap_items.sort(
        key=lambda item: item["absolute_contribution"],
        reverse=True,
    )

    # ---------------------------------------------------------
    # Separate factors increasing/decreasing fraud probability
    #
    # Positive SHAP:
    #     pushes prediction toward Fraud
    #
    # Negative SHAP:
    #     pushes prediction toward Legitimate
    # ---------------------------------------------------------

    fraud_factors = [
        item
        for item in shap_items
        if item["contribution"] > 0
    ]

    legitimate_factors = [
        item
        for item in shap_items
        if item["contribution"] < 0
    ]

    fraud_factors.sort(
        key=lambda item: item["contribution"],
        reverse=True,
    )

    legitimate_factors.sort(
        key=lambda item: abs(item["contribution"]),
        reverse=True,
    )

    # ---------------------------------------------------------
    # Build readable factor descriptions
    # ---------------------------------------------------------

    key_factors = []

    if normalized_prediction == "fraud":

        # Strongest factors increasing fraud probability
        for item in fraud_factors[:3]:

            feature = item["feature"]
            description = _feature_name(feature)
            value = features.get(feature)

            if value is not None:

                key_factors.append(
                    f"{description.capitalize()} "
                    f"({ _format_value(feature, value) }) "
                    f"contributed toward a higher fraud probability."
                )

            else:

                key_factors.append(
                    f"{description.capitalize()} "
                    f"contributed toward a higher fraud probability."
                )

        # Mention one strong counter-factor if available
        if legitimate_factors:

            item = legitimate_factors[0]
            feature = item["feature"]
            description = _feature_name(feature)

            key_factors.append(
                f"{description.capitalize()} "
                f"contributed toward a lower fraud probability."
            )

        # -----------------------------------------------------
        # Summary
        # -----------------------------------------------------

        if key_factors:

            summary = (
                "The transaction was classified as fraud because "
                "the strongest model contributions increased its "
                "estimated fraud probability."
            )

        else:

            summary = (
                "The transaction was classified as fraud based on "
                "the overall pattern of the supplied transaction features."
            )

    else:

        # Strongest factors decreasing fraud probability
        for item in legitimate_factors[:3]:

            feature = item["feature"]
            description = _feature_name(feature)
            value = features.get(feature)

            if value is not None:

                key_factors.append(
                    f"{description.capitalize()} "
                    f"({ _format_value(feature, value) }) "
                    f"contributed toward a lower fraud probability."
                )

            else:

                key_factors.append(
                    f"{description.capitalize()} "
                    f"contributed toward a lower fraud probability."
                )

        # Mention one strong fraud-increasing factor
        if fraud_factors:

            item = fraud_factors[0]
            feature = item["feature"]
            description = _feature_name(feature)

            key_factors.append(
                f"{description.capitalize()} "
                f"contributed toward a higher fraud probability."
            )

        # -----------------------------------------------------
        # Summary
        # -----------------------------------------------------

        if key_factors:

            summary = (
                "The transaction was classified as legitimate because "
                "the strongest model contributions reduced its estimated "
                "fraud probability."
            )

        else:

            summary = (
                "The transaction was classified as legitimate based on "
                "the overall pattern of the supplied transaction features."
            )

    # ---------------------------------------------------------
    # Confidence wording
    # ---------------------------------------------------------

    if normalized_prediction == "fraud":
        probability = fraud_probability
    else:
        probability = legitimate_probability

    confidence_text = (
        f"The model assigned a "
        f"{probability * 100:.1f}% probability to the predicted class."
    )

    return {
        "summary": summary,
        "confidence_text": confidence_text,
        "key_factors": key_factors,
        "interpretation_note": (
            "These factors describe how the model's feature "
            "contributions influenced the prediction. They should "
            "not be interpreted as proof of causation."
        ),
    }