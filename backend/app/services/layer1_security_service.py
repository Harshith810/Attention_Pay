from backend.app.models.transaction import Transaction
from backend.app.services.security_service import (
    check_api_route_integrity,
    check_impossible_travel,
)


def run_layer1_security_checks(
    transaction: Transaction,
) -> dict:
    """
    Runs all Layer 1 backend security checks and
    returns one unified security decision.
    """

    # Run API route integrity check
    api_route_result = check_api_route_integrity(
        transaction
    )

    # Run impossible travel check
    impossible_travel_result = check_impossible_travel(
        transaction
    )

    checks = {
        "api_route_integrity": api_route_result,
        "impossible_travel": impossible_travel_result,
    }

    # If any Layer 1 security rule fails,
    # block the transaction.
    failed_checks = [
        result
        for result in checks.values()
        if not result["passed"]
    ]

    if failed_checks:
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
        }

    # All Layer 1 checks passed.
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
    }