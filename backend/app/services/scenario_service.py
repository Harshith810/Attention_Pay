from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.models.transaction import Transaction

VALID_SCENARIOS = {
    "normal_transaction",
    "impossible_travel",
    "api_route_tampering",
    "behaviour_fraud",
    "random_transaction",
}


def get_random_transaction(
    db: Session,
    scenario: str,
) -> Transaction | None:

    # Validate the requested selection mode
    if scenario not in VALID_SCENARIOS:
        raise ValueError(
            f"Invalid scenario: {scenario}"
        )

    query = db.query(Transaction)

    # Random Transaction:
    # select from the complete demo pool
    if scenario == "random_transaction":
        return (
            query
            .order_by(func.random())
            .first()
        )

    # Named scenario:
    # filter matching rows, then randomly select one
    return (
        query
        .filter(Transaction.scenario == scenario)
        .order_by(func.random())
        .first()
    )

def get_transaction_by_id(
    db: Session,
    transaction_id: str,
) -> Transaction | None:
    """
    Retrieve one transaction using its transaction ID.
    """

    return (
        db.query(Transaction)
        .filter(
            Transaction.transaction_id
            == transaction_id
        )
        .first()
    )