#!/usr/bin/env python3
"""
Seed 3 Realistic Test Fraud Complaints into PostgreSQL (bank_fraud_portal)
Usage: python insert_test_complaints.py
"""

from datetime import datetime, timedelta
import random

def insert_three():
    from server import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now()

    complaints = [
        {
            "ticket_number": f"FRD-2026-LIVE-8801",
            "customer_id": 1,
            "customer_name": "Arjun Singhal",
            "account_number": "ACT-1102-9901",
            "incident_type": "Unauthorized UPI QR Code Phishing",
            "amount_involved": 48500.00,
            "recovered_amount": 0.0,
            "incident_date": now - timedelta(minutes=7),
            "reported_channel": "Mobile Banking Alert",
            "severity": "HIGH",
            "status": "UNDER_INVESTIGATION",
            "assigned_investigator": "Andrew (SOC Operations)",
            "suspect_entity": "PayTM_Merchant_Fake_902",
            "description": "Customer scanned QR code sent via WhatsApp claiming to receive refund; Rs 48,500 debited.",
            "action_taken": "Dispatched SOC alert; placed debit freeze on suspected recipient handle."
        },
        {
            "ticket_number": f"FRD-2026-LIVE-8802",
            "customer_id": 2,
            "customer_name": "Kavita Krishnamurthy",
            "account_number": "ACT-2244-8812",
            "incident_type": "International Card Not Present (CNP) Compromise",
            "amount_involved": 125000.00,
            "recovered_amount": 0.0,
            "incident_date": now - timedelta(minutes=4),
            "reported_channel": "Branch Phone Alert",
            "severity": "CRITICAL",
            "status": "UNDER_INVESTIGATION",
            "assigned_investigator": "Andrew (SOC Operations)",
            "suspect_entity": "Overseas POS London GB",
            "description": "3 high-value unauthorized foreign currency transactions attempted on card while customer was in Bengaluru.",
            "action_taken": "International usage blocked immediately; card hotlisted."
        },
        {
            "ticket_number": f"FRD-2026-LIVE-8803",
            "customer_id": 3,
            "customer_name": "Rohan Deshpande",
            "account_number": "ACT-3388-7711",
            "incident_type": "Vendor Impersonation Wire Fraud (Business Email Compromise)",
            "amount_involved": 310000.00,
            "recovered_amount": 0.0,
            "incident_date": now - timedelta(minutes=1),
            "reported_channel": "Corporate NetBanking Portal",
            "severity": "CRITICAL",
            "status": "UNDER_INVESTIGATION",
            "assigned_investigator": "Andrew (SOC Operations)",
            "suspect_entity": "Spoofed Invoice Domain: punelogistlcs.com",
            "description": "Accountant received altered invoice requesting RTGS transfer to new beneficiary bank account.",
            "action_taken": "Beneficiary account frozen at destination bank; RTGS recall initiated."
        }
    ]

    inserted = 0
    for c in complaints:
        cursor.execute("""
            INSERT INTO fraud_tickets (
                ticket_number, customer_id, customer_name, account_number, incident_type,
                amount_involved, recovered_amount, incident_date, reported_channel,
                severity, status, assigned_investigator, suspect_entity, description, action_taken
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (ticket_number) DO UPDATE SET
                status = EXCLUDED.status,
                incident_date = EXCLUDED.incident_date,
                amount_involved = EXCLUDED.amount_involved;
        """, (
            c["ticket_number"], c["customer_id"], c["customer_name"], c["account_number"],
            c["incident_type"], c["amount_involved"], c["recovered_amount"], c["incident_date"],
            c["reported_channel"], c["severity"], c["status"], c["assigned_investigator"],
            c["suspect_entity"], c["description"], c["action_taken"]
        ))
        inserted += 1

    conn.commit()
    cursor.close()
    conn.close()
    print(f"[+] Successfully inserted {inserted} test fraud complaints into PostgreSQL!")
    print("    1. FRD-2026-LIVE-8801 - Arjun Singhal (Rs. 48,500 - UPI QR Phishing)")
    print("    2. FRD-2026-LIVE-8802 - Kavita Krishnamurthy (Rs. 1,25,000 - Card Compromise)")
    print("    3. FRD-2026-LIVE-8803 - Rohan Deshpande (Rs. 3,10,000 - Vendor Wire Fraud)")

if __name__ == "__main__":
    insert_three()
