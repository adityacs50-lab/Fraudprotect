import requests
import time
import json
import os

API_URL = "http://localhost:8000/api"

def run_e2e_scenario():
    print("1. Generating a new batch of transactions...")
    res = requests.post(f"{API_URL}/stream?n=50")
    if res.status_code != 200:
        print(f"Error streaming: {res.text}")
        return
    data = res.json()
    print(f"Streamed 50 txs. Flagged: {data['flagged']}")
    
    print("\n2. Fetching alerts queue...")
    res = requests.get(f"{API_URL}/alerts?status=pending")
    alerts = res.json().get("alerts", [])
    if not alerts:
        print("No pending alerts found. Try streaming more.")
        return
    
    alert = alerts[0]
    alert_id = alert["alert_id"]
    tx_id = alert["transaction_id"]
    print(f"Found pending alert {alert_id} for transaction {tx_id} (Amount: ${alert['amount']})")
    
    print("\n3. Fetching transaction details & explanations...")
    res = requests.get(f"{API_URL}/transactions/{tx_id}")
    tx_detail = res.json()
    reasons = [r['rule_name'] for r in tx_detail.get('reason_codes', [])]
    print(f"Decision: {tx_detail['decision']}")
    print(f"Reason Codes: {reasons}")
    print(f"Fraud Probability: {tx_detail['fraud_probability']:.2f}")
    
    print("\n4. Analyst taking action (Confirm Fraud)...")
    payload = {
        "action": "confirm_fraud",
        "notes": "Confirmed stolen card based on velocity spike.",
        "analyst_id": "analyst-e2e"
    }
    res = requests.post(f"{API_URL}/alerts/{alert_id}/action", json=payload)
    print(f"Action response: {res.json()}")
    
    print("\n5. Verifying alert is resolved...")
    res = requests.get(f"{API_URL}/alerts?status=resolved")
    resolved = res.json().get("alerts", [])
    found = any(a['id'] == alert_id for a in resolved)
    print(f"Alert {alert_id} found in resolved queue? {found}")

if __name__ == "__main__":
    run_e2e_scenario()
