import math
from backend.app.models.transaction import Transaction




def check_api_route_integrity(
    transaction: Transaction,
) -> dict:
    """
    Verifies that the actual API endpoint matches
    the expected API endpoint.
    """

    expected_endpoint = transaction.expected_api_endpoint
    actual_endpoint = transaction.actual_api_endpoint

    passed = expected_endpoint == actual_endpoint

    if passed:
        return {
            "check": "api_route_integrity",
            "passed": True,
            "status": "PASS",
            "reason": (
                "API route matches the expected endpoint."
            ),
            "expected_endpoint": expected_endpoint,
            "actual_endpoint": actual_endpoint,
        }

    return {
        "check": "api_route_integrity",
        "passed": False,
        "status": "BLOCK",
        "reason": (
            "API route integrity violation detected. "
            "Actual endpoint does not match the expected endpoint."
        ),
        "expected_endpoint": expected_endpoint,
        "actual_endpoint": actual_endpoint,
    }


# Maximum realistic travel speed in km/h.
# We can keep this as a named constant so it is easy
# to configure later.
MAX_TRAVEL_SPEED_KMH = 1000


def calculate_distance_km(
    latitude_1: float,
    longitude_1: float,
    latitude_2: float,
    longitude_2: float,
) -> float:
    """
    Calculate geographic distance between two
    latitude/longitude coordinates using Haversine.
    """

    earth_radius_km = 6371.0

    latitude_1_rad = math.radians(latitude_1)
    longitude_1_rad = math.radians(longitude_1)

    latitude_2_rad = math.radians(latitude_2)
    longitude_2_rad = math.radians(longitude_2)

    latitude_difference = (
        latitude_2_rad - latitude_1_rad
    )

    longitude_difference = (
        longitude_2_rad - longitude_1_rad
    )

    haversine_value = (
        math.sin(latitude_difference / 2) ** 2
        + math.cos(latitude_1_rad)
        * math.cos(latitude_2_rad)
        * math.sin(longitude_difference / 2) ** 2
    )

    central_angle = (
        2
        * math.atan2(
            math.sqrt(haversine_value),
            math.sqrt(1 - haversine_value),
        )
    )

    return earth_radius_km * central_angle


def check_impossible_travel(
    transaction: Transaction,
) -> dict:
    """
    Detect whether the required travel speed between
    two transaction locations exceeds the allowed limit.
    """

    distance_km = calculate_distance_km(
        transaction.previous_latitude,
        transaction.previous_longitude,
        transaction.current_latitude,
        transaction.current_longitude,
    )

    time_difference = (
        transaction.current_transaction_timestamp
        - transaction.previous_transaction_timestamp
    )

    time_difference_hours = (
        time_difference.total_seconds() / 3600
    )

    # Defensive handling for invalid timestamps.
    if time_difference_hours <= 0:
        return {
            "check": "impossible_travel",
            "passed": False,
            "status": "BLOCK",
            "reason": (
                "Invalid transaction timestamps detected."
            ),
            "distance_km": round(distance_km, 2),
            "time_difference_hours": round(
                time_difference_hours,
                4,
            ),
            "required_speed_kmh": None,
            "max_allowed_speed_kmh": (
                MAX_TRAVEL_SPEED_KMH
            ),
        }

    required_speed_kmh = (
        distance_km / time_difference_hours
    )

    passed = (
        required_speed_kmh
        <= MAX_TRAVEL_SPEED_KMH
    )

    if passed:
        return {
            "check": "impossible_travel",
            "passed": True,
            "status": "PASS",
            "reason": (
                "Travel speed is within the allowed limit."
            ),
            "distance_km": round(distance_km, 2),
            "time_difference_hours": round(
                time_difference_hours,
                4,
            ),
            "required_speed_kmh": round(
                required_speed_kmh,
                2,
            ),
            "max_allowed_speed_kmh": (
                MAX_TRAVEL_SPEED_KMH
            ),
        }

    return {
        "check": "impossible_travel",
        "passed": False,
        "status": "BLOCK",
        "reason": (
            "Impossible travel detected. "
            "Required travel speed exceeds the allowed limit."
        ),
        "distance_km": round(distance_km, 2),
        "time_difference_hours": round(
            time_difference_hours,
            4,
        ),
        "required_speed_kmh": round(
            required_speed_kmh,
            2,
        ),
        "max_allowed_speed_kmh": (
            MAX_TRAVEL_SPEED_KMH
        ),
    }


def check_api_route_integrity(
    transaction: Transaction,
) -> dict:
    """
    Verifies that the actual API endpoint matches
    the expected API endpoint.
    """

    expected_endpoint = transaction.expected_api_endpoint
    actual_endpoint = transaction.actual_api_endpoint

    passed = expected_endpoint == actual_endpoint

    if passed:
        return {
            "check": "api_route_integrity",
            "passed": True,
            "status": "PASS",
            "reason": (
                "API route matches the expected endpoint."
            ),
            "expected_endpoint": expected_endpoint,
            "actual_endpoint": actual_endpoint,
        }

    return {
        "check": "api_route_integrity",
        "passed": False,
        "status": "BLOCK",
        "reason": (
            "API route integrity violation detected. "
            "Actual endpoint does not match the expected endpoint."
        ),
        "expected_endpoint": expected_endpoint,
        "actual_endpoint": actual_endpoint,
    }