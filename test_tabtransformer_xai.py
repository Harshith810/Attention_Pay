from backend.app.services.fraud_detection import fraud_detection_service


test_transaction = {
    "known_device_flag": 1,
    "device_changed_flag": 0,
    "device_type": "mobile",
    "browser_name": "chrome",
    "operating_system": "android",
    "transactions_last_1min": 0,
    "transactions_last_5min": 2,
    "transactions_last_10min": 3,
    "transaction_amount": 2912.81,
    "previous_transaction_amount": 648.77,
    "session_risk_score": 0.29,
}


print("\n==============================")
print("TABTRANSFORMER PREDICTION")
print("==============================")

prediction = fraud_detection_service.predict(
    test_transaction
)

print(prediction)


print("\n==============================")
print("SHAP + LIME EXPLANATION")
print("==============================")

explanation = fraud_detection_service.explain(
    test_transaction
)

print(explanation)