"""Step 5 end-to-end XAI API test.

Run while the FastAPI backend is running:
    python test_step5_api.py

This test intentionally treats scenario selection as input metadata, not as
an expected ML label. Behaviour Fraud may be classified Fraud or Legitimate;
the test only verifies that Layer 1 passed and Layer 2 XAI executed.
"""

import sys
import requests

BASE_URL = "http://127.0.0.1:8000"

PHISHING_URL = "https://secure-paypal-login.example.com/verify/account"
LEGITIMATE_URL = "https://www.google.com"
SCENARIOS = [
    "normal_transaction",
    "impossible_travel",
    "api_route_tampering",
    "behaviour_fraud",
]


def request(method, path, **kwargs):
    response = requests.request(
        method,
        f"{BASE_URL}{path}",
        timeout=120,
        **kwargs,
    )
    print(f"{method} {path} -> {response.status_code}")
    if response.status_code >= 400:
        print(response.text)
        raise AssertionError(f"Request failed: {response.status_code}")
    return response.json()


def main():
    print("\n=== STEP 5: STAGE 1 ===")

    phishing = request(
        "POST",
        "/api/v1/analyze/url",
        json={"url": PHISHING_URL},
    )

    assert phishing["blocked"] is True
    assert phishing["explanation_source"] == "bert_url"
    assert phishing["explanation"] is not None
    assert phishing["explanation"]["type"] == "bert_url_explanation"
    assert phishing["stage2_access_token"] is None

    legitimate = request(
        "POST",
        "/api/v1/analyze/url",
        json={"url": LEGITIMATE_URL},
    )

    assert legitimate["blocked"] is False
    assert legitimate["stage2_access_token"]
    assert legitimate["explanation_source"] is None
    assert legitimate["explanation"] is None

    token = legitimate["stage2_access_token"]
    headers = {"X-Stage2-Access-Token": token}

    print("\n=== STEP 5: STAGE 2 SCENARIOS ===")

    for scenario in SCENARIOS:
        print(f"\n--- {scenario} ---")

        preview = request(
            "POST",
            "/api/v1/simulate/transaction",
            headers=headers,
            json={"scenario": scenario},
        )

        transaction_id = preview["transaction_id"]
        assert transaction_id

        result = request(
            "POST",
            f"/api/v1/simulate/transaction/{transaction_id}/process",
            headers=headers,
        )

        if scenario in {"impossible_travel", "api_route_tampering"}:
            assert result["decision"] == "BLOCK"
            assert result["ai_executed"] is False
            assert result["explanation_source"] == "backend_rule"
            assert result["explanation"] is not None
            assert result["ai_result"] is None
            print("PASS: Layer 1 blocked + backend rule explanation + AI skipped")
        else:
            assert result["ai_executed"] is True
            assert result["explanation_source"] == "tabtransformer_xai"
            assert result["explanation"] is not None
            assert result["explanation"]["type"] == "tabtransformer_xai"
            assert result["prediction"] in {"Fraud", "Legitimate"}
            assert result["fraud_probability"] is not None
            assert result["legitimate_probability"] is not None
            assert result["explanation"]["features"]
            assert result["features"] is not None
            print("PASS: Layer 2 prediction + SHAP/LIME explanation")

    print("\n=== STEP 5 COMPLETE ===")
    print("All Stage 1 and Stage 2 XAI API assertions passed.")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, requests.RequestException) as exc:
        print(f"\nFAILED: {exc}")
        sys.exit(1)
