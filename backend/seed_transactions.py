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


def generate_ordered_velocity(
    velocity_1_range,
    velocity_5_range,
    velocity_10_range,
):
    """
    Generate transaction velocity values while guaranteeing:

        transactions_last_1min
        <=
        transactions_last_5min
        <=
        transactions_last_10min

    The supplied ranges still control the scenario-specific
    magnitude and randomness.
    """

    v1 = random.randint(*velocity_1_range)

    v5_min = max(
        velocity_5_range[0],
        v1,
    )

    v5_max = velocity_5_range[1]

    if v5_min > v5_max:
        raise ValueError(
            "Invalid velocity ranges: "
            "5-minute range cannot accommodate the generated "
            "1-minute value."
        )

    v5 = random.randint(
        v5_min,
        v5_max,
    )

    v10_min = max(
        velocity_10_range[0],
        v5,
    )

    v10_max = velocity_10_range[1]

    if v10_min > v10_max:
        raise ValueError(
            "Invalid velocity ranges: "
            "10-minute range cannot accommodate the generated "
            "5-minute value."
        )

    v10 = random.randint(
        v10_min,
        v10_max,
    )

    return v1, v5, v10


def safe_location_pair():
    """
    Returns two nearby locations.

    Used for transactions that should PASS
    Impossible Travel detection.
    """

    base_latitude = random.uniform(
        12.8,
        13.1,
    )

    base_longitude = random.uniform(
        77.4,
        77.8,
    )

    previous_latitude = base_latitude
    previous_longitude = base_longitude

    current_latitude = (
        base_latitude
        + random.uniform(-0.03, 0.03)
    )

    current_longitude = (
        base_longitude
        + random.uniform(-0.03, 0.03)
    )

    return (
        previous_latitude,
        previous_longitude,
        current_latitude,
        current_longitude,
    )


# -------------------------------------------------
# DEMO LOCATION DATA
# -------------------------------------------------

# Recognizable locations used only for the transaction-location
# simulation. Coordinates are used by the existing Layer 1
# impossible-travel calculation and can also be displayed by
# the frontend map later.
DEMO_LOCATIONS = [
    ("Bengaluru, India", 12.9716, 77.5946),
    ("Mumbai, India", 19.0760, 72.8777),
    ("Delhi, India", 28.6139, 77.2090),
    ("Chennai, India", 13.0827, 80.2707),
    ("Hyderabad, India", 17.3850, 78.4867),
    ("Pune, India", 18.5204, 73.8567),
    ("Kolkata, India", 22.5726, 88.3639),
    ("Ahmedabad, India", 23.0225, 72.5714),
    ("Jaipur, India", 26.9124, 75.7873),
    ("Kochi, India", 9.9312, 76.2673),
    ("Singapore", 1.3521, 103.8198),
    ("Dubai, UAE", 25.2048, 55.2708),
    ("London, UK", 51.5074, -0.1278),
    ("Paris, France", 48.8566, 2.3522),
    ("Frankfurt, Germany", 50.1109, 8.6821),
    ("Tokyo, Japan", 35.6762, 139.6503),
    ("Sydney, Australia", -33.8688, 151.2093),
    ("Toronto, Canada", 43.6532, -79.3832),
    ("New York, USA", 40.7128, -74.0060),
    ("San Francisco, USA", 37.7749, -122.4194),
    ("Bangkok, Thailand", 13.7563, 100.5018),
    ("Kuala Lumpur, Malaysia", 3.1390, 101.6869),
    ("Amsterdam, Netherlands", 52.3676, 4.9041),
    ("Zurich, Switzerland", 47.3769, 8.5417),
    ("Doha, Qatar", 25.2854, 51.5310),
    ("Hong Kong", 22.3193, 114.1694),
    ("Seoul, South Korea", 37.5665, 126.9780),
    ("Rome, Italy", 41.9028, 12.4964),
    ("Madrid, Spain", 40.4168, -3.7038),
    ("Cape Town, South Africa", -33.9249, 18.4241),
]


def location_coordinates(location):
    """Return latitude and longitude from a demo location tuple."""
    return location[1], location[2]


def generate_possible_travel_pair(index: int):
    """
    Return two different recognizable locations for a transaction
    whose movement remains physically plausible within the generated
    timestamp gap.

    A pool of 45 unique city-to-city pairs is used so the Normal,
    API Route Tampering, and Behaviour Fraud scenarios do not reuse
    the same geographic pair.
    """
    locations = {
        "Bengaluru, India": (12.9716, 77.5946),
        "Mysuru, India": (12.2958, 76.6394),
        "Mumbai, India": (19.0760, 72.8777),
        "Pune, India": (18.5204, 73.8567),
        "Delhi, India": (28.6139, 77.2090),
        "Jaipur, India": (26.9124, 75.7873),
        "Chennai, India": (13.0827, 80.2707),
        "Hyderabad, India": (17.3850, 78.4867),
        "Vijayawada, India": (16.5062, 80.6480),
        "Kolkata, India": (22.5726, 88.3639),
        "Durgapur, India": (23.5204, 87.3119),
        "Ahmedabad, India": (23.0225, 72.5714),
        "Udaipur, India": (24.5854, 73.7125),
        "Kochi, India": (9.9312, 76.2673),
        "Coimbatore, India": (11.0168, 76.9558),
        "Chandigarh, India": (30.7333, 76.7794),
        "Bhubaneswar, India": (20.2961, 85.8245),
        "Goa, India": (15.4909, 73.8278),
        "Nagpur, India": (21.1458, 79.0882),
        "Lucknow, India": (26.8467, 80.9462),
        "Indore, India": (22.7196, 75.8577),
        "Surat, India": (21.1702, 72.8311),
        "Patna, India": (25.5941, 85.1376),
        "Visakhapatnam, India": (17.6868, 83.2185),
        "Bhopal, India": (23.2599, 77.4126),
    }

    possible_pairs = [
        ("Bengaluru, India", "Mysuru, India"),
        ("Mumbai, India", "Pune, India"),
        ("Delhi, India", "Jaipur, India"),
        ("Chennai, India", "Bengaluru, India"),
        ("Hyderabad, India", "Vijayawada, India"),
        ("Kolkata, India", "Durgapur, India"),
        ("Ahmedabad, India", "Udaipur, India"),
        ("Kochi, India", "Coimbatore, India"),
        ("Pune, India", "Mumbai, India"),
        ("Jaipur, India", "Delhi, India"),
        ("Bengaluru, India", "Hyderabad, India"),
        ("Chennai, India", "Hyderabad, India"),
        ("Mumbai, India", "Ahmedabad, India"),
        ("Delhi, India", "Chandigarh, India"),
        ("Kolkata, India", "Bhubaneswar, India"),

        ("Goa, India", "Mumbai, India"),
        ("Nagpur, India", "Bhopal, India"),
        ("Lucknow, India", "Delhi, India"),
        ("Indore, India", "Ahmedabad, India"),
        ("Surat, India", "Mumbai, India"),
        ("Patna, India", "Kolkata, India"),
        ("Visakhapatnam, India", "Bhubaneswar, India"),
        ("Bhopal, India", "Indore, India"),
        ("Mysuru, India", "Coimbatore, India"),
        ("Vijayawada, India", "Chennai, India"),

        ("Bengaluru, India", "Goa, India"),
        ("Pune, India", "Surat, India"),
        ("Jaipur, India", "Udaipur, India"),
        ("Delhi, India", "Lucknow, India"),
        ("Hyderabad, India", "Nagpur, India"),
        ("Chennai, India", "Coimbatore, India"),
        ("Kochi, India", "Goa, India"),
        ("Ahmedabad, India", "Surat, India"),
        ("Kolkata, India", "Patna, India"),
        ("Mumbai, India", "Indore, India"),

        ("Bengaluru, India", "Chennai, India"),
        ("Hyderabad, India", "Visakhapatnam, India"),
        ("Delhi, India", "Agra, India"),
        ("Pune, India", "Nashik, India"),
        ("Kolkata, India", "Ranchi, India"),
        ("Chandigarh, India", "Jaipur, India"),
        ("Lucknow, India", "Kanpur, India"),
        ("Nagpur, India", "Raipur, India"),
        ("Bhopal, India", "Indore, India"),
        ("Surat, India", "Vadodara, India"),
    ]

    # Use the pair index directly. The three callers pass offsets
    # of 0, 15, and 30 respectively.
    origin_name, destination_name = possible_pairs[index - 1]

    return (
        origin_name,
        destination_name,
        locations.get(origin_name, DEMO_LOCATIONS[0][1:]),
        locations.get(destination_name, DEMO_LOCATIONS[0][1:]),
    )


def generate_impossible_travel_pair(index: int):
    """
    Return two different, geographically distant demo locations.

    The timestamp gap used by the impossible-travel scenario is
    intentionally short, so the existing Layer 1 speed calculation
    will classify the movement as impossible.
    """
    impossible_pairs = [
        ("Bengaluru, India", "London, UK"),
        ("Mumbai, India", "Tokyo, Japan"),
        ("Delhi, India", "New York, USA"),
        ("Chennai, India", "Toronto, Canada"),
        ("Hyderabad, India", "Paris, France"),
        ("Pune, India", "Sydney, Australia"),
        ("Kolkata, India", "Frankfurt, Germany"),
        ("Ahmedabad, India", "Singapore"),
        ("Kochi, India", "Dubai, UAE"),
        ("Jaipur, India", "San Francisco, USA"),
        ("Bengaluru, India", "Amsterdam, Netherlands"),
        ("Mumbai, India", "Seoul, South Korea"),
        ("Delhi, India", "Rome, Italy"),
        ("Chennai, India", "Zurich, Switzerland"),
        ("Hyderabad, India", "Cape Town, South Africa"),
    ]

    locations = {
        name: (latitude, longitude)
        for name, latitude, longitude in DEMO_LOCATIONS
    }

    origin_name, destination_name = impossible_pairs[
        (index - 1) % len(impossible_pairs)
    ]

    return (
        origin_name,
        destination_name,
        locations[origin_name],
        locations[destination_name],
    )


# -------------------------------------------------
# NORMAL TRANSACTIONS
# -------------------------------------------------

def create_normal_transactions():

    transactions = []

    for i in range(
        1,
        ROWS_PER_SCENARIO + 1,
    ):

        device_type, browser_name, operating_system = (
            random_device()
        )

        (
            previous_place,
            current_place,
            previous_coordinates,
            current_coordinates,
        ) = generate_possible_travel_pair(i)

        previous_latitude, previous_longitude = previous_coordinates
        current_latitude, current_longitude = current_coordinates

        current_time = (
            datetime.now()
            - timedelta(
                minutes=random.randint(1, 5000)
            )
        )

        # Keep enough time between transactions for the selected
        # city-to-city movement to remain physically plausible.
        previous_time = (
            current_time
            - timedelta(
                hours=random.randint(3, 48)
            )
        )

        amount = round(
            random.uniform(
                100,
                5000,
            ),
            2,
        )

        (
            transactions_last_1min,
            transactions_last_5min,
            transactions_last_10min,
        ) = generate_ordered_velocity(
            (0, 2),
            (1, 4),
            (1, 6),
        )

        transactions.append(
            Transaction(
                transaction_id=generate_transaction_id("N"),
                scenario="normal_transaction",

                receiver_identifier=(
                    f"merchant_{random.randint(1000, 9999)}"
                ),

                transaction_amount=amount,

                previous_transaction_amount=round(
                    random.uniform(
                        100,
                        5000,
                    ),
                    2,
                ),

                transactions_last_1min=(
                    transactions_last_1min
                ),

                transactions_last_5min=(
                    transactions_last_5min
                ),

                transactions_last_10min=(
                    transactions_last_10min
                ),

                known_device_flag=True,
                device_changed_flag=False,

                device_type=device_type,
                browser_name=browser_name,
                operating_system=operating_system,

                session_risk_score=round(
                    random.uniform(
                        0.05,
                        0.30,
                    ),
                    2,
                ),

                previous_latitude=previous_latitude,
                previous_longitude=previous_longitude,

                current_latitude=current_latitude,
                current_longitude=current_longitude,

                previous_transaction_timestamp=(
                    previous_time
                ),

                current_transaction_timestamp=(
                    current_time
                ),

                expected_api_endpoint=random.choice(
                    EXPECTED_ENDPOINTS
                ),

                actual_api_endpoint=(
                    EXPECTED_ENDPOINTS[0]
                ),
            )
        )

        transactions[-1].actual_api_endpoint = (
            transactions[-1].expected_api_endpoint
        )

    return transactions


# -------------------------------------------------
# IMPOSSIBLE TRAVEL TRANSACTIONS
# -------------------------------------------------

def create_impossible_travel_transactions():

    transactions = []

    for i in range(
        1,
        ROWS_PER_SCENARIO + 1,
    ):

        device_type, browser_name, operating_system = (
            random_device()
        )

        (
            previous_place,
            current_place,
            previous_coordinates,
            current_coordinates,
        ) = generate_impossible_travel_pair(i)

        previous_latitude, previous_longitude = previous_coordinates
        current_latitude, current_longitude = current_coordinates

        current_time = (
            datetime.now()
            - timedelta(
                minutes=random.randint(1, 5000)
            )
        )

        previous_time = (
            current_time
            - timedelta(
                minutes=random.randint(5, 30)
            )
        )

        expected_endpoint = random.choice(
            EXPECTED_ENDPOINTS
        )

        (
            transactions_last_1min,
            transactions_last_5min,
            transactions_last_10min,
        ) = generate_ordered_velocity(
            (0, 3),
            (1, 5),
            (2, 7),
        )

        transactions.append(
            Transaction(
                transaction_id=generate_transaction_id("T"),

                scenario="impossible_travel",

                receiver_identifier=(
                    f"merchant_{random.randint(1000, 9999)}"
                ),

                transaction_amount=round(
                    random.uniform(
                        500,
                        10000,
                    ),
                    2,
                ),

                previous_transaction_amount=round(
                    random.uniform(
                        100,
                        5000,
                    ),
                    2,
                ),

                transactions_last_1min=(
                    transactions_last_1min
                ),

                transactions_last_5min=(
                    transactions_last_5min
                ),

                transactions_last_10min=(
                    transactions_last_10min
                ),

                known_device_flag=True,
                device_changed_flag=False,

                device_type=device_type,
                browser_name=browser_name,
                operating_system=operating_system,

                session_risk_score=round(
                    random.uniform(
                        0.20,
                        0.50,
                    ),
                    2,
                ),

                # Different recognizable origin/destination
                # for every generated impossible-travel transaction.
                previous_latitude=previous_latitude,
                previous_longitude=previous_longitude,
                current_latitude=current_latitude,
                current_longitude=current_longitude,

                previous_transaction_timestamp=(
                    previous_time
                ),

                current_transaction_timestamp=(
                    current_time
                ),

                expected_api_endpoint=(
                    expected_endpoint
                ),

                actual_api_endpoint=(
                    expected_endpoint
                ),
            )
        )

    return transactions


# -------------------------------------------------
# API ROUTE TAMPERING TRANSACTIONS
# -------------------------------------------------

def create_api_tampering_transactions():

    transactions = []

    for i in range(
        1,
        ROWS_PER_SCENARIO + 1,
    ):

        device_type, browser_name, operating_system = (
            random_device()
        )

        (
            previous_place,
            current_place,
            previous_coordinates,
            current_coordinates,
        ) = generate_possible_travel_pair(i + ROWS_PER_SCENARIO)

        previous_latitude, previous_longitude = previous_coordinates
        current_latitude, current_longitude = current_coordinates

        current_time = (
            datetime.now()
            - timedelta(
                minutes=random.randint(1, 5000)
            )
        )

        previous_time = (
            current_time
            - timedelta(
                hours=random.randint(3, 48)
            )
        )

        expected_endpoint = random.choice(
            EXPECTED_ENDPOINTS
        )

        actual_endpoint = random.choice(
            TAMPERED_ENDPOINTS
        )

        (
            transactions_last_1min,
            transactions_last_5min,
            transactions_last_10min,
        ) = generate_ordered_velocity(
            (0, 3),
            (1, 5),
            (2, 8),
        )

        transactions.append(
            Transaction(
                transaction_id=generate_transaction_id("A"),

                scenario="api_route_tampering",

                receiver_identifier=(
                    f"merchant_{random.randint(1000, 9999)}"
                ),

                transaction_amount=round(
                    random.uniform(
                        100,
                        8000,
                    ),
                    2,
                ),

                previous_transaction_amount=round(
                    random.uniform(
                        100,
                        5000,
                    ),
                    2,
                ),

                transactions_last_1min=(
                    transactions_last_1min
                ),

                transactions_last_5min=(
                    transactions_last_5min
                ),

                transactions_last_10min=(
                    transactions_last_10min
                ),

                known_device_flag=True,
                device_changed_flag=False,

                device_type=device_type,
                browser_name=browser_name,
                operating_system=operating_system,

                session_risk_score=round(
                    random.uniform(
                        0.10,
                        0.40,
                    ),
                    2,
                ),

                previous_latitude=previous_latitude,
                previous_longitude=previous_longitude,

                current_latitude=current_latitude,
                current_longitude=current_longitude,

                previous_transaction_timestamp=(
                    previous_time
                ),

                current_transaction_timestamp=(
                    current_time
                ),

                expected_api_endpoint=(
                    expected_endpoint
                ),

                actual_api_endpoint=(
                    actual_endpoint
                ),
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

    for i, profile in enumerate(fraud_profiles, start=1):

        device_type, browser_name, operating_system = (
            random_device()
        )

        (
            previous_place,
            current_place,
            previous_coordinates,
            current_coordinates,
        ) = generate_possible_travel_pair(
            i + (2 * ROWS_PER_SCENARIO)
        )

        previous_latitude, previous_longitude = previous_coordinates
        current_latitude, current_longitude = current_coordinates

        current_time = (
            datetime.now()
            - timedelta(
                minutes=random.randint(1, 5000)
            )
        )

        previous_time = (
            current_time
            - timedelta(
                hours=random.randint(3, 48)
            )
        )

        expected_endpoint = random.choice(
            EXPECTED_ENDPOINTS
        )

        (
            transactions_last_1min,
            transactions_last_5min,
            transactions_last_10min,
        ) = generate_ordered_velocity(
            profile["velocity_1"],
            profile["velocity_5"],
            profile["velocity_10"],
        )

        transactions.append(
            Transaction(
                transaction_id=generate_transaction_id("B"),

                scenario="behaviour_fraud",

                receiver_identifier=(
                    f"merchant_{random.randint(1000, 9999)}"
                ),

                transaction_amount=round(
                    random.uniform(
                        *profile["amount"]
                    ),
                    2,
                ),

                previous_transaction_amount=round(
                    random.uniform(
                        *profile["previous_amount"]
                    ),
                    2,
                ),

                transactions_last_1min=(
                    transactions_last_1min
                ),

                transactions_last_5min=(
                    transactions_last_5min
                ),

                transactions_last_10min=(
                    transactions_last_10min
                ),

                known_device_flag=(
                    profile["known_device"]
                ),

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

                previous_transaction_timestamp=(
                    previous_time
                ),

                current_transaction_timestamp=(
                    current_time
                ),

                # Layer 1 API integrity check should pass
                expected_api_endpoint=(
                    expected_endpoint
                ),

                actual_api_endpoint=(
                    expected_endpoint
                ),
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
        print(
            f"Total transactions: {len(transactions)}"
        )

    except Exception as error:

        db.rollback()

        print()
        print("Database seeding failed!")
        print(error)

    finally:

        db.close()


if __name__ == "__main__":
    seed_database()