from backend.app.models.transaction import Transaction
from backend.app.services.security_service import (
    check_api_route_integrity,
    check_impossible_travel,
)


def build_rule_explanation(
    failed_checks: list[dict],
) -> dict:
    """
    Builds a standardized explanation for the Layer 1
    security rule that caused the transaction to be blocked.
    """

    # Prefer API route tampering if it failed.
    for result in failed_checks:
        if result["check"] == "api_route_integrity":
            return {
                "explanation_source": "backend_rule",
                "explanation": {
                    "type": "api_route_tampering",
                    "summary": (
                        "Transaction blocked because the requested "
                        "API route does not match the expected route."
                    ),
                    "details": {
                        "expected_endpoint": result.get(
                            "expected_endpoint"
                        ),
                        "actual_endpoint": result.get(
                            "actual_endpoint"
                        ),
                    },
                },
            }

    # Impossible Travel explanation.
    for result in failed_checks:
        if result["check"] == "impossible_travel":

            # Invalid timestamp case
            if result.get("required_speed_kmh") is None:
                summary = (
                    "Transaction blocked because the transaction "
                    "timestamps are invalid."
                )

            else:
                summary = (
                    "Transaction blocked because the required "
                    "travel speed exceeds the configured security threshold."
                )

            return {
                "explanation_source": "backend_rule",
                "explanation": {
                    "type": "impossible_travel",
                    "summary": summary,
                    "details": {
                        "distance_km": result.get(
                            "distance_km"
                        ),
                        "elapsed_hours": result.get(
                            "time_difference_hours"
                        ),
                        "required_speed_kmh": result.get(
                            "required_speed_kmh"
                        ),
                        "maximum_allowed_speed_kmh": result.get(
                            "max_allowed_speed_kmh"
                        ),
                    },
                },
            }

    return {
        "explanation_source": "backend_rule",
        "explanation": {
            "type": "layer1_security_rule",
            "summary": (
                "Transaction blocked by a Layer 1 backend "
                "security rule."
            ),
            "details": {},
        },
    }


def run_layer1_security_checks(
    transaction: Transaction,
) -> dict:
    """
    Runs all Layer 1 backend security checks and
    returns one unified security decision.
    """

    # ---------------------------------------------------------
    # 1. API Route Integrity
    # ---------------------------------------------------------

    api_route_result = check_api_route_integrity(
        transaction
    )

    # ---------------------------------------------------------
    # 2. Impossible Travel
    # ---------------------------------------------------------

    impossible_travel_result = check_impossible_travel(
        transaction
    )

    checks = {
        "api_route_integrity": api_route_result,
        "impossible_travel": impossible_travel_result,
    }

    # ---------------------------------------------------------
    # 3. Find failed checks
    # ---------------------------------------------------------

    failed_checks = [
        result
        for result in checks.values()
        if not result["passed"]
    ]

    # ---------------------------------------------------------
    # 4. BLOCK if any Layer 1 rule fails
    # ---------------------------------------------------------

    if failed_checks:

        rule_explanation = build_rule_explanation(
            failed_checks
        )

        return {
            "layer": "layer_1_security",
            "passed": False,
            "decision": "BLOCK",
            "reason": (
                "Transaction blocked by Layer 1 "
                "security checks."
            ),
            "failed_checks": [
                result["check"]
                for result in failed_checks
            ],
            "checks": checks,

            # Step 3 XAI
            **rule_explanation,
        }

    # ---------------------------------------------------------
    # 5. All Layer 1 checks passed
    # ---------------------------------------------------------

    return {
        "layer": "layer_1_security",
        "passed": True,
        "decision": "CONTINUE",
        "reason": (
            "All Layer 1 security checks passed. "
            "Transaction can continue to Layer 2."
        ),
        "failed_checks": [],
        "checks": checks,

        # No explanation is needed because no rule
        # blocked the transaction.
        "explanation_source": None,
        "explanation": None,
    }