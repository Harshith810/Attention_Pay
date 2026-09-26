from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db

from backend.app.services.scenario_service import (
    VALID_SCENARIOS,
    get_random_transaction,
    get_transaction_by_id,
)

from backend.app.schemas.transaction import (
    TransactionPreview,
    TransactionProcessingResponse,
    TransactionScenarioRequest,
)

from backend.app.services.layer1_security_service import (
    run_layer1_security_checks,
)

from backend.app.dependencies.stage_access import (
    require_stage2_access,
)

from backend.app.services.feature_engineering import (
    feature_engineering_service,
)

from backend.app.services.fraud_detection import (
    fraud_detection_service,
)


router = APIRouter(
    prefix="/api/v1/simulate",
    tags=["Stage 2 Simulation"],
)


@router.post(
    "/transaction",
    response_model=TransactionPreview,
)
def simulate_transaction(
    request: TransactionScenarioRequest,
    db: Session = Depends(get_db),
    stage2_access_token: str = Depends(
        require_stage2_access
    ),
):
    scenario = request.scenario

    # Validate requested scenario
    if scenario not in VALID_SCENARIOS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Invalid scenario.",
                "valid_scenarios": sorted(VALID_SCENARIOS),
            },
        )

    # Retrieve transaction from PostgreSQL
    transaction = get_random_transaction(
        db=db,
        scenario=scenario,
    )

    # No transaction available
    if transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": (
                    "No transaction found "
                    "for the requested scenario."
                )
            },
        )

    return {
        "transaction_id": transaction.transaction_id,
        "selection_mode": scenario,

        "receiver_identifier": (
            transaction.receiver_identifier
        ),

        "transaction_amount": (
            transaction.transaction_amount
        ),

        "previous_transaction_amount": (
            transaction.previous_transaction_amount
        ),

        "transactions_last_1min": (
            transaction.transactions_last_1min
        ),

        "transactions_last_5min": (
            transaction.transactions_last_5min
        ),

        "transactions_last_10min": (
            transaction.transactions_last_10min
        ),

        "known_device_flag": (
            transaction.known_device_flag
        ),

        "device_changed_flag": (
            transaction.device_changed_flag
        ),

        "device_type": transaction.device_type,
        "browser_name": transaction.browser_name,

        "operating_system": (
            transaction.operating_system
        ),

        "session_risk_score": (
            transaction.session_risk_score
        ),

        "previous_latitude": (
            transaction.previous_latitude
        ),

        "previous_longitude": (
            transaction.previous_longitude
        ),

        "current_latitude": (
            transaction.current_latitude
        ),

        "current_longitude": (
            transaction.current_longitude
        ),

        "previous_transaction_timestamp": (
            transaction.previous_transaction_timestamp
        ),

        "current_transaction_timestamp": (
            transaction.current_transaction_timestamp
        ),

        "expected_api_endpoint": (
            transaction.expected_api_endpoint
        ),

        "actual_api_endpoint": (
            transaction.actual_api_endpoint
        ),
    }

@router.post(
    "/transaction/{transaction_id}/process",
    response_model=TransactionProcessingResponse,
)
def process_transaction(
    transaction_id: str,
    db: Session = Depends(get_db),
    stage2_access_token: str = Depends(
        require_stage2_access
    ),
):
    """
    Retrieve the transaction and process it through:

    Layer 1:
        - API Route Integrity
        - Impossible Travel

    If Layer 1 blocks the transaction:
        - Stop immediately.
        - Do not execute Layer 2 AI.

    If Layer 1 passes:
        - Feature Engineering
        - TabTransformer fraud detection
    """

    # ---------------------------------------------------------
    # 1. Retrieve transaction
    # ---------------------------------------------------------

    transaction = get_transaction_by_id(
        db=db,
        transaction_id=transaction_id,
    )

    if transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": "Transaction not found."
            },
        )

    # ---------------------------------------------------------
    # 2. Layer 1 security checks
    # ---------------------------------------------------------

    layer1_result = run_layer1_security_checks(
        transaction
    )

    # ---------------------------------------------------------
    # 3. BLOCK immediately if Layer 1 fails
    #
    # IMPORTANT:
    # TabTransformer must NOT execute here.
    # ---------------------------------------------------------

    if layer1_result["decision"] == "BLOCK":

        return {
            "transaction_id": transaction.transaction_id,
            **layer1_result,
            "ai_executed": False,
            "features": None,
            "ai_result": None,
        }

    # ---------------------------------------------------------
    # 4. Feature Engineering
    #
    # Only reached when Layer 1 passes.
    # ---------------------------------------------------------

    features = (
        feature_engineering_service.from_transaction(
            transaction
        )
    )

    # ---------------------------------------------------------
    # 5. TabTransformer inference
    # ---------------------------------------------------------

    ai_result = (
        fraud_detection_service.predict(
            features
        )
    )

    # ---------------------------------------------------------
    # 6. Determine final decision
    # ---------------------------------------------------------

    if ai_result["prediction"] == "Fraud":

        decision = "BLOCK"

        passed = False

        reason = (
            "Transaction passed Layer 1 security checks "
            "but was classified as fraud by the "
            "TabTransformer."
        )

    else:

        decision = "CONTINUE"

        passed = True

        reason = (
            "Transaction passed Layer 1 security checks "
            "and was classified as legitimate by the "
            "TabTransformer."
        )

    # ---------------------------------------------------------
    # 7. Final response
    # ---------------------------------------------------------

    return {
        "transaction_id": transaction.transaction_id,

        "layer": "layer_2_fraud_detection",

        "passed": passed,

        "decision": decision,

        "reason": reason,

        "failed_checks": layer1_result[
            "failed_checks"
        ],

        "checks": layer1_result[
            "checks"
        ],

        "ai_executed": True,

        "features": features,

        "ai_result": ai_result,
    }