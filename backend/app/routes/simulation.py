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
    Retrieve the transaction from PostgreSQL and
    process it through Layer 1 security checks.
    """

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

    result = run_layer1_security_checks(
        transaction
    )

    return {
        "transaction_id": transaction.transaction_id,
        **result,
    }