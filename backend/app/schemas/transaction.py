from datetime import datetime
from typing import Any

from pydantic import BaseModel


class TransactionScenarioRequest(BaseModel):
    scenario: str


class TransactionPreview(BaseModel):
    transaction_id: str
    selection_mode: str

    receiver_identifier: str

    transaction_amount: float
    previous_transaction_amount: float

    transactions_last_1min: int
    transactions_last_5min: int
    transactions_last_10min: int

    known_device_flag: bool
    device_changed_flag: bool

    device_type: str
    browser_name: str
    operating_system: str

    session_risk_score: float

    previous_latitude: float
    previous_longitude: float

    current_latitude: float
    current_longitude: float

    previous_transaction_timestamp: datetime
    current_transaction_timestamp: datetime

    expected_api_endpoint: str
    actual_api_endpoint: str

    model_config = {
        "from_attributes": True
    }


class TransactionProcessingResponse(BaseModel):
    transaction_id: str

    layer: str
    passed: bool
    decision: str
    reason: str

    failed_checks: list[str]

    checks: dict[str, dict[str, Any]]