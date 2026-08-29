import random
from datetime import datetime, timedelta

from backend.app.database import SessionLocal
from backend.app.models.transaction import Transaction


# -------------------------------------------------
# CONFIGURATION
# -------------------------------------------------

ROWS_PER_SCENARIO = 15

EXPECTED_ENDPOINTS = [
    "/api/v1/payments/process",
    "/api/v1/transactions/process",
    "/api/v1/payment/authorize",
]

TAMPERED_ENDPOINTS = [
    "/api/v1/admin/payment/process",
    "/api/v1/payments/bypass",
    "/api/v1/debug/transaction",
]

DEVICES = [
    ("mobile", "Chrome Mobile", "Android"),
    ("mobile", "Safari", "iOS"),
    ("desktop", "Chrome", "Windows"),
    ("desktop", "Firefox", "Windows"),
    ("desktop", "Safari", "macOS"),
]


# -------------------------------------------------
# HELPER FUNCTIONS
# -------------------------------------------------

def generate_transaction_id(prefix: str) -> str:
    """
    Generate a transaction ID using a scenario-specific
    prefix letter followed by random digits.
    """

    random_part = random.randint(
        10000000,
        99999999,
    )

    return f"{prefix}{random_part}"


def random_device():
    return random.choice(DEVICES)


def safe_location_pair():
    """
    Returns two nearby locations.

    Used for transactions that should PASS
    Impossible Travel detection.
    """

    base_latitude = random.uniform(12.8, 13.1)
    base_longitude = random.uniform(77.4, 77.8)

    previous_latitude = base_latitude
    previous_longitude = base_longitude

    current_latitude = base_latitude + random.uniform(-0.03, 0.03)
    current_longitude = base_longitude + random.uniform(-0.03, 0.03)

    return (
        previous_latitude,
        previous_longitude,
        current_latitude,
        current_longitude,
    )


# -------------------------------------------------
# NORMAL TRANSACTIONS
# -------------------------------------------------

def create_normal_transactions():

    transactions = []

    for i in range(1, ROWS_PER_SCENARIO + 1):

        device_type, browser_name, operating_system = random_device()

        (
            previous_latitude,
            previous_longitude,
            current_latitude,
            current_longitude,
        ) = safe_location_pair()

        current_time = datetime.now() - timedelta(
            minutes=random.randint(1, 5000)
        )

        previous_time = current_time - timedelta(
            hours=random.randint(1, 48)
        )

        amount = round(random.uniform(100, 5000), 2)

        transactions.append(
            Transaction(
                transaction_id=generate_transaction_id("N"),
                scenario="normal_transaction",
                receiver_identifier=f"merchant_{random.randint(1000, 9999)}",

                transaction_amount=amount,
                previous_transaction_amount=round(
                    random.uniform(100, 5000),
                    2,
                ),

                transactions_last_1min=random.randint(0, 2),
                transactions_last_5min=random.randint(1, 4),
                transactions_last_10min=random.randint(1, 6),

                known_device_flag=True,
                device_changed_flag=False,

                device_type=device_type,
                browser_name=browser_name,
                operating_system=operating_system,

                session_risk_score=round(
                    random.uniform(0.05, 0.30),
                    2,
                ),

                previous_latitude=previous_latitude,
                previous_longitude=previous_longitude,

                current_latitude=current_latitude,
                current_longitude=current_longitude,

                previous_transaction_timestamp=previous_time,
                current_transaction_timestamp=current_time,

                expected_api_endpoint=random.choice(
                    EXPECTED_ENDPOINTS
                ),
                actual_api_endpoint=EXPECTED_ENDPOINTS[0],
            )
        )

        # Ensure expected endpoint matches actual endpoint.
        transactions[-1].actual_api_endpoint = (
            transactions[-1].expected_api_endpoint
        )

    return transactions


# -------------------------------------------------
# IMPOSSIBLE TRAVEL TRANSACTIONS
# -------------------------------------------------

def create_impossible_travel_transactions():

    transactions = []

    for i in range(1, ROWS_PER_SCENARIO + 1):

        device_type, browser_name, operating_system = random_device()

        current_time = datetime.now() - timedelta(
            minutes=random.randint(1, 5000)
        )

        # Only minutes apart
        previous_time = current_time - timedelta(
            minutes=random.randint(5, 30)
        )

        expected_endpoint = random.choice(EXPECTED_ENDPOINTS)

        transactions.append(
            Transaction(
                transaction_id=generate_transaction_id("T"),

                scenario="impossible_travel",

                receiver_identifier=(
                    f"merchant_{random.randint(1000, 9999)}"
                ),

                transaction_amount=round(
                    random.uniform(500, 10000),
                    2,
                ),

                previous_transaction_amount=round(
                    random.uniform(100, 5000),
                    2,
                ),

                transactions_last_1min=random.randint(0, 3),
                transactions_last_5min=random.randint(1, 5),
                transactions_last_10min=random.randint(2, 7),

                known_device_flag=True,
                device_changed_flag=False,

                device_type=device_type,
                browser_name=browser_name,
                operating_system=operating_system,

                session_risk_score=round(
                    random.uniform(0.20, 0.50),
                    2,
                ),

                # Bengaluru
                previous_latitude=12.9716,
                previous_longitude=77.5946,

                # London
                current_latitude=51.5074,
                current_longitude=-0.1278,

                previous_transaction_timestamp=previous_time,
                current_transaction_timestamp=current_time,

                expected_api_endpoint=expected_endpoint,
                actual_api_endpoint=expected_endpoint,
            )
        )

    return transactions


# -------------------------------------------------
# API ROUTE TAMPERING TRANSACTIONS
# -------------------------------------------------

def create_api_tampering_transactions():

    transactions = []

    for i in range(1, ROWS_PER_SCENARIO + 1):

        device_type, browser_name, operating_system = random_device()

        (
            previous_latitude,
            previous_longitude,
            current_latitude,
            current_longitude,
        ) = safe_location_pair()

        current_time = datetime.now() - timedelta(
            minutes=random.randint(1, 5000)
        )

        previous_time = current_time - timedelta(
            hours=random.randint(1, 48)
        )

        expected_endpoint = random.choice(EXPECTED_ENDPOINTS)

        actual_endpoint = random.choice(TAMPERED_ENDPOINTS)

        transactions.append(
            Transaction(
                transaction_id=generate_transaction_id("A"),

                scenario="api_route_tampering",

                receiver_identifier=(
                    f"merchant_{random.randint(1000, 9999)}"
                ),

                transaction_amount=round(
                    random.uniform(100, 8000),
                    2,
                ),

                previous_transaction_amount=round(
                    random.uniform(100, 5000),
                    2,
                ),

                transactions_last_1min=random.randint(0, 3),
                transactions_last_5min=random.randint(1, 5),
                transactions_last_10min=random.randint(2, 8),

                known_device_flag=True,
                device_changed_flag=False,

                device_type=device_type,
                browser_name=browser_name,
                operating_system=operating_system,

                session_risk_score=round(
                    random.uniform(0.10, 0.40),
                    2,
                ),

                previous_latitude=previous_latitude,
                previous_longitude=previous_longitude,

                current_latitude=current_latitude,
                current_longitude=current_longitude,

                previous_transaction_timestamp=previous_time,
                current_transaction_timestamp=current_time,

                expected_api_endpoint=expected_endpoint,
                actual_api_endpoint=actual_endpoint,
            )
        )

    return transactions


# -------------------------------------------------
# BEHAVIOUR FRAUD TRANSACTIONS
# -------------------------------------------------

def create_behaviour_fraud_transactions():

    transactions = []

    # Each profile represents a different synthetic
    # behavioural anomaly pattern.
    fraud_profiles = [

        # 1. Extreme multi-signal anomaly
        {
            "amount": (100000, 250000),
            "previous_amount": (100, 2000),
            "velocity_1": (10, 15),
            "velocity_5": (25, 40),
            "velocity_10": (45, 70),
            "known_device": False,
            "device_changed": True,
            "session_risk": (0.90, 0.99),
        },

        # 2. Velocity-heavy anomaly
        {
            "amount": (1000, 8000),
            "previous_amount": (800, 7000),
            "velocity_1": (10, 15),
            "velocity_5": (25, 40),
            "velocity_10": (45, 70),
            "known_device": True,
            "device_changed": False,
            "session_risk": (0.55, 0.70),
        },

        # 3. Transaction-heavy anomaly
        {
            "amount": (80000, 200000),
            "previous_amount": (100, 3000),
            "velocity_1": (0, 2),
            "velocity_5": (1, 4),
            "velocity_10": (2, 7),
            "known_device": True,
            "device_changed": False,
            "session_risk": (0.50, 0.70),
        },

        # 4. Device anomaly
        {
            "amount": (1000, 8000),
            "previous_amount": (800, 7000),
            "velocity_1": (0, 2),
            "velocity_5": (1, 4),
            "velocity_10": (2, 7),
            "known_device": False,
            "device_changed": True,
            "session_risk": (0.75, 0.90),
        },

        # 5. Session-risk-heavy anomaly
        {
            "amount": (3000, 15000),
            "previous_amount": (1000, 8000),
            "velocity_1": (0, 2),
            "velocity_5": (1, 4),
            "velocity_10": (2, 7),
            "known_device": True,
            "device_changed": False,
            "session_risk": (0.90, 0.99),
        },

        # 6. Velocity + transaction anomaly
        {
            "amount": (40000, 100000),
            "previous_amount": (500, 5000),
            "velocity_1": (7, 12),
            "velocity_5": (15, 30),
            "velocity_10": (25, 50),
            "known_device": True,
            "device_changed": False,
            "session_risk": (0.55, 0.75),
        },

        # 7. Device + transaction anomaly
        {
            "amount": (50000, 120000),
            "previous_amount": (500, 5000),
            "velocity_1": (0, 3),
            "velocity_5": (1, 5),
            "velocity_10": (2, 8),
            "known_device": False,
            "device_changed": True,
            "session_risk": (0.55, 0.75),
        },

        # 8. Velocity + device anomaly
        {
            "amount": (1000, 8000),
            "previous_amount": (800, 7000),
            "velocity_1": (7, 12),
            "velocity_5": (15, 30),
            "velocity_10": (25, 50),
            "known_device": False,
            "device_changed": True,
            "session_risk": (0.60, 0.80),
        },

        # 9. Transaction + session anomaly
        {
            "amount": (50000, 150000),
            "previous_amount": (500, 5000),
            "velocity_1": (0, 2),
            "velocity_5": (1, 4),
            "velocity_10": (2, 7),
            "known_device": True,
            "device_changed": False,
            "session_risk": (0.85, 0.98),
        },

        # 10. Velocity + session anomaly
        {
            "amount": (1000, 8000),
            "previous_amount": (800, 7000),
            "velocity_1": (7, 12),
            "velocity_5": (15, 30),
            "velocity_10": (25, 50),
            "known_device": True,
            "device_changed": False,
            "session_risk": (0.85, 0.98),
        },

        # 11. Device + session anomaly
        {
            "amount": (1000, 8000),
            "previous_amount": (800, 7000),
            "velocity_1": (0, 2),
            "velocity_5": (1, 4),
            "velocity_10": (2, 7),
            "known_device": False,
            "device_changed": True,
            "session_risk": (0.85, 0.98),
        },

        # 12. Moderate distributed anomalies
        {
            "amount": (15000, 35000),
            "previous_amount": (1000, 7000),
            "velocity_1": (4, 7),
            "velocity_5": (8, 15),
            "velocity_10": (12, 25),
            "known_device": False,
            "device_changed": True,
            "session_risk": (0.60, 0.75),
        },

        # 13. Mixed categorical/environment anomaly
        {
            "amount": (20000, 50000),
            "previous_amount": (1000, 8000),
            "velocity_1": (4, 8),
            "velocity_5": (10, 20),
            "velocity_10": (15, 30),
            "known_device": False,
            "device_changed": True,
            "session_risk": (0.75, 0.90),
        },

        # 14. Known-device behavioural anomaly
        {
            "amount": (15000, 40000),
            "previous_amount": (1000, 8000),
            "velocity_1": (8, 14),
            "velocity_5": (18, 35),
            "velocity_10": (30, 55),
            "known_device": True,
            "device_changed": False,
            "session_risk": (0.80, 0.95),
        },

        # 15. Mixed multi-signal anomaly
        {
            "amount": (30000, 90000),
            "previous_amount": (500, 6000),
            "velocity_1": (5, 10),
            "velocity_5": (12, 25),
            "velocity_10": (20, 40),
            "known_device": False,
            "device_changed": True,
            "session_risk": (0.75, 0.95),
        },
    ]

    for profile in fraud_profiles:

        device_type, browser_name, operating_system = (
            random_device()
        )

        (
            previous_latitude,
            previous_longitude,
            current_latitude,
            current_longitude,
        ) = safe_location_pair()

        current_time = datetime.now() - timedelta(
            minutes=random.randint(1, 5000)
        )

        previous_time = current_time - timedelta(
            hours=random.randint(2, 48)
        )

        expected_endpoint = random.choice(
            EXPECTED_ENDPOINTS
        )

        transactions.append(
            Transaction(
                transaction_id=generate_transaction_id("B"),

                scenario="behaviour_fraud",

                receiver_identifier=(
                    f"merchant_{random.randint(1000, 9999)}"
                ),

                transaction_amount=round(
                    random.uniform(*profile["amount"]),
                    2,
                ),

                previous_transaction_amount=round(
                    random.uniform(
                        *profile["previous_amount"]
                    ),
                    2,
                ),

                transactions_last_1min=random.randint(
                    *profile["velocity_1"]
                ),

                transactions_last_5min=random.randint(
                    *profile["velocity_5"]
                ),

                transactions_last_10min=random.randint(
                    *profile["velocity_10"]
                ),

                known_device_flag=profile["known_device"],

                device_changed_flag=(
                    profile["device_changed"]
                ),

                device_type=device_type,
                browser_name=browser_name,
                operating_system=operating_system,

                session_risk_score=round(
                    random.uniform(
                        *profile["session_risk"]
                    ),
                    2,
                ),

                # Layer 1 impossible-travel check should pass
                previous_latitude=previous_latitude,
                previous_longitude=previous_longitude,

                current_latitude=current_latitude,
                current_longitude=current_longitude,

                previous_transaction_timestamp=previous_time,
                current_transaction_timestamp=current_time,

                # Layer 1 API integrity check should pass
                expected_api_endpoint=expected_endpoint,
                actual_api_endpoint=expected_endpoint,
            )
        )

    return transactions


# -------------------------------------------------
# MAIN SEED FUNCTION
# -------------------------------------------------

def seed_database():

    db = SessionLocal()

    try:

        # Remove existing demo records so the script
        # can be run repeatedly without duplicates.
        deleted_count = (
            db.query(Transaction)
            .delete()
        )

        print(
            f"Removed {deleted_count} existing transaction records."
        )

        transactions = []

        transactions.extend(
            create_normal_transactions()
        )

        transactions.extend(
            create_impossible_travel_transactions()
        )

        transactions.extend(
            create_api_tampering_transactions()
        )

        transactions.extend(
            create_behaviour_fraud_transactions()
        )

        db.add_all(transactions)

        db.commit()

        print()
        print("Database seeded successfully!")
        print(
            f"Normal transactions: {ROWS_PER_SCENARIO}"
        )
        print(
            f"Impossible travel transactions: "
            f"{ROWS_PER_SCENARIO}"
        )
        print(
            f"API route tampering transactions: "
            f"{ROWS_PER_SCENARIO}"
        )
        print(
            f"Behaviour fraud transactions: "
            f"{ROWS_PER_SCENARIO}"
        )
        print("-" * 40)
        print(f"Total transactions: {len(transactions)}")

    except Exception as error:

        db.rollback()

        print()
        print("Database seeding failed!")
        print(error)

    finally:

        db.close()


if __name__ == "__main__":
    seed_database()