"""
proof_no_label_leakage.py
 
This file contains ONLY urls, no "expected" labels anywhere.
Run this to prove the model's predictions come purely from its own
understanding of the URL, not from any hint in the test script.
"""
 
from url_detection_service import predict_url
 
urls_only = [
    "https://www.wikipedia.org",
    "https://www.swiggy.com",
    "http://sbi-kyc-update-verify.info/login",
    "https://accounts-google-secure-verification.com",
    "https://www.isro.gov.in",
    "https://amazon-prize-winner-claim-now.online",
]
 
for url in urls_only:
    result = predict_url(url)
    print(f"{url:55} -> {result['prediction']:12} (confidence: {result['confidence']})")