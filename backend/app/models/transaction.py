from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.database import Base

class Transaction(Base):
    __tablename__ = "transaction_simulations"

    # -------------------------------------------------
    # IDENTIFICATION / SCENARIO
    # -------------------------------------------------

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    transaction_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
    )

    scenario: Mapped[str] = mapped_column(
        String(50),
        index=True,
    )

    receiver_identifier: Mapped[str] = mapped_column(
        String(100),
    )

    # -------------------------------------------------
    # TRANSACTION DETAILS
    # -------------------------------------------------

    transaction_amount: Mapped[float] = mapped_column(
        Float,
    )

    previous_transaction_amount: Mapped[float] = mapped_column(
        Float,
    )

    # -------------------------------------------------
    # TRANSACTION VELOCITY
    # FUTURE TABTRANSFORMER FEATURES
    # -------------------------------------------------

    transactions_last_1min: Mapped[int] = mapped_column(
        Integer,
    )

    transactions_last_5min: Mapped[int] = mapped_column(
        Integer,
    )

    transactions_last_10min: Mapped[int] = mapped_column(
        Integer,
    )

    # -------------------------------------------------
    # DEVICE FEATURES
    # -------------------------------------------------

    known_device_flag: Mapped[bool] = mapped_column(
        Boolean,
    )

    device_changed_flag: Mapped[bool] = mapped_column(
        Boolean,
    )

    device_type: Mapped[str] = mapped_column(
        String(30),
    )

    browser_name: Mapped[str] = mapped_column(
        String(30),
    )

    operating_system: Mapped[str] = mapped_column(
        String(30),
    )

    # -------------------------------------------------
    # SESSION RISK
    # -------------------------------------------------

    session_risk_score: Mapped[float] = mapped_column(
        Float,
    )

    # -------------------------------------------------
    # IMPOSSIBLE TRAVEL DATA
    # NOT TABTRANSFORMER FEATURES
    # -------------------------------------------------

    previous_latitude: Mapped[float] = mapped_column(
        Float,
    )

    previous_longitude: Mapped[float] = mapped_column(
        Float,
    )

    current_latitude: Mapped[float] = mapped_column(
        Float,
    )

    current_longitude: Mapped[float] = mapped_column(
        Float,
    )

    previous_transaction_timestamp: Mapped[datetime] = mapped_column(
        DateTime,
    )

    current_transaction_timestamp: Mapped[datetime] = mapped_column(
        DateTime,
    )

    # -------------------------------------------------
    # API ROUTING VERIFICATION
    # NOT TABTRANSFORMER FEATURES
    # -------------------------------------------------

    expected_api_endpoint: Mapped[str] = mapped_column(
        String(255),
    )

    actual_api_endpoint: Mapped[str] = mapped_column(
        String(255),
    )