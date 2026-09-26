from typing import Any, Dict

from backend.app.models.transaction import Transaction


class FeatureEngineeringService:
    """
    Converts a database Transaction object into the exact
    11-feature input contract expected by the TabTransformer.

    Important:
    - Does NOT modify the database row.
    - Does NOT use the scenario or label.
    - Does NOT include Impossible Travel or API Route Integrity.
    - Produces only the 11 canonical model features.
    """

    # Canonical categorical values expected by the trained model
    VALID_DEVICE_TYPES = {
        "desktop",
        "mobile",
        "tablet",
    }

    VALID_BROWSERS = {
        "chrome",
        "firefox",
        "edge",
        "safari",
    }

    VALID_OPERATING_SYSTEMS = {
        "android",
        "ios",
        "windows",
        "macos",
        "linux",
    }

    @staticmethod
    def _normalize(value: Any) -> str:
        """
        Normalize a categorical database value.

        Example:
            "Chrome" -> "chrome"
            " iOS "  -> "ios"
        """
        if value is None:
            raise ValueError("Categorical feature cannot be None.")

        return str(value).strip().lower()

    @classmethod
    def _normalize_device_type(cls, value: Any) -> str:
        value = cls._normalize(value)

        if value not in cls.VALID_DEVICE_TYPES:
            raise ValueError(
                f"Unsupported device_type '{value}'. "
                f"Expected one of: {sorted(cls.VALID_DEVICE_TYPES)}"
            )

        return value

    @classmethod
    def _normalize_browser(cls, value: Any) -> str:
        value = cls._normalize(value)

        # Handle common database/display variations.
        browser_aliases = {
            "chrome mobile": "chrome",
            "google chrome": "chrome",
            "mozilla firefox": "firefox",
            "microsoft edge": "edge",
            "apple safari": "safari",
        }

        value = browser_aliases.get(value, value)

        if value not in cls.VALID_BROWSERS:
            raise ValueError(
                f"Unsupported browser_name '{value}'. "
                f"Expected one of: {sorted(cls.VALID_BROWSERS)}"
            )

        return value

    @classmethod
    def _normalize_operating_system(cls, value: Any) -> str:
        value = cls._normalize(value)

        os_aliases = {
            "windows 10": "windows",
            "windows 11": "windows",
            "win": "windows",
            "mac": "macos",
            "mac os": "macos",
            "mac os x": "macos",
            "apple ios": "ios",
        }

        value = os_aliases.get(value, value)

        if value not in cls.VALID_OPERATING_SYSTEMS:
            raise ValueError(
                f"Unsupported operating_system '{value}'. "
                f"Expected one of: {sorted(cls.VALID_OPERATING_SYSTEMS)}"
            )

        return value

    @staticmethod
    def _validate_binary(value: Any, feature_name: str) -> int:
        """
        Validate a binary feature and return it as int 0/1.
        """
        try:
            value = int(value)
        except (TypeError, ValueError):
            raise ValueError(
                f"{feature_name} must be 0 or 1."
            )

        if value not in (0, 1):
            raise ValueError(
                f"{feature_name} must be 0 or 1, got {value}."
            )

        return value

    @staticmethod
    def _validate_non_negative(value: Any, feature_name: str) -> float:
        """
        Validate a numerical feature that cannot be negative.
        """
        try:
            value = float(value)
        except (TypeError, ValueError):
            raise ValueError(
                f"{feature_name} must be numeric."
            )

        if value < 0:
            raise ValueError(
                f"{feature_name} cannot be negative."
            )

        return value

    @classmethod
    def from_transaction(cls, transaction: Transaction) -> Dict[str, Any]:
        """
        Convert a SQLAlchemy Transaction object into the canonical
        11-feature TabTransformer input dictionary.
        """

        # ---------------------------------------------------------
        # 1. Binary features
        # ---------------------------------------------------------

        known_device_flag = cls._validate_binary(
            transaction.known_device_flag,
            "known_device_flag",
        )

        device_changed_flag = cls._validate_binary(
            transaction.device_changed_flag,
            "device_changed_flag",
        )

        # ---------------------------------------------------------
        # 2. Categorical features
        # ---------------------------------------------------------

        device_type = cls._normalize_device_type(
            transaction.device_type
        )

        browser_name = cls._normalize_browser(
            transaction.browser_name
        )

        operating_system = cls._normalize_operating_system(
            transaction.operating_system
        )

        # ---------------------------------------------------------
        # 3. Numerical features
        # ---------------------------------------------------------

        transactions_last_1min = cls._validate_non_negative(
            transaction.transactions_last_1min,
            "transactions_last_1min",
        )

        transactions_last_5min = cls._validate_non_negative(
            transaction.transactions_last_5min,
            "transactions_last_5min",
        )

        transactions_last_10min = cls._validate_non_negative(
            transaction.transactions_last_10min,
            "transactions_last_10min",
        )

        transaction_amount = cls._validate_non_negative(
            transaction.transaction_amount,
            "transaction_amount",
        )

        previous_transaction_amount = cls._validate_non_negative(
            transaction.previous_transaction_amount,
            "previous_transaction_amount",
        )

        session_risk_score = float(transaction.session_risk_score)

        # Current model contract uses a 0–1 session risk score.
        if not 0.0 <= session_risk_score <= 1.0:
            raise ValueError(
                "session_risk_score must be between 0.0 and 1.0, "
                f"got {session_risk_score}."
            )

        # ---------------------------------------------------------
        # 4. Velocity consistency
        # ---------------------------------------------------------

        if not (
            transactions_last_1min
            <= transactions_last_5min
            <= transactions_last_10min
        ):
            raise ValueError(
                "Transaction velocity must satisfy: "
                "transactions_last_1min <= "
                "transactions_last_5min <= "
                "transactions_last_10min."
            )

        # ---------------------------------------------------------
        # 5. Final canonical 11-feature vector
        # ---------------------------------------------------------

        features = {
            "known_device_flag": known_device_flag,
            "device_changed_flag": device_changed_flag,
            "device_type": device_type,
            "browser_name": browser_name,
            "operating_system": operating_system,
            "transactions_last_1min": transactions_last_1min,
            "transactions_last_5min": transactions_last_5min,
            "transactions_last_10min": transactions_last_10min,
            "transaction_amount": transaction_amount,
            "previous_transaction_amount": previous_transaction_amount,
            "session_risk_score": session_risk_score,
        }

        return features


# Singleton service
feature_engineering_service = FeatureEngineeringService()