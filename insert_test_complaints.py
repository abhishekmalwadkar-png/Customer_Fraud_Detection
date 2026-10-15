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
        },
        # 2025 Multi-Year Historical Records
        {
            "ticket_number": "FRD-2025-HIST-101", "customer_id": 1, "customer_name": "Arjun Singhal", "account_number": "ACT-1102-9901",
            "incident_type": "SIM Swap & NetBanking Hijacking", "amount_involved": 185000.0, "recovered_amount": 45000.0,
            "incident_date": datetime(2025, 11, 14, 10, 30), "reported_channel": "Mobile Helpline", "severity": "CRITICAL",
            "status": "RESOLVED", "assigned_investigator": "Andrew (SOC Operations)", "suspect_entity": "eSIM Clone Server",
            "description": "Customer SIM deactivated without consent.", "action_taken": "SIM cancelled, funds recalled."
        },
        {
            "ticket_number": "FRD-2025-HIST-102", "customer_id": 2, "customer_name": "Kavita Krishnamurthy", "account_number": "ACT-2244-8812",
            "incident_type": "Fake Electricity Bill SMS Scam", "amount_involved": 15000.0, "recovered_amount": 15000.0,
            "incident_date": datetime(2025, 8, 22, 14, 15), "reported_channel": "SMS Alert", "severity": "MEDIUM",
            "status": "RESOLVED", "assigned_investigator": "Andrew (SOC Operations)", "suspect_entity": "Fake MSEDCL Portal",
            "description": "Customer paid fake bill via SMS link.", "action_taken": "Merchant handle frozen; full refund credited."
        },
        {
            "ticket_number": "FRD-2025-HIST-103", "customer_id": 3, "customer_name": "Rohan Deshpande", "account_number": "ACT-3388-7711",
            "incident_type": "UPI Payment QR Code Phishing", "amount_involved": 52000.0, "recovered_amount": 52000.0,
            "incident_date": datetime(2025, 9, 5, 16, 40), "reported_channel": "Mobile App Alert", "severity": "HIGH",
            "status": "RESOLVED", "assigned_investigator": "Andrew (SOC Operations)", "suspect_entity": "QuickMerchant APK",
            "description": "Phishing QR code scanned at local store.", "action_taken": "Nodal bank freeze successful."
        },
        {
            "ticket_number": "FRD-2025-HIST-104", "customer_id": 4, "customer_name": "Ananya Sen", "account_number": "ACT-4455-6622",
            "incident_type": "ATM Card Skimming & Cloned PIN Replay", "amount_involved": 40000.0, "recovered_amount": 40000.0,
            "incident_date": datetime(2025, 6, 12, 11, 20), "reported_channel": "Branch Visit", "severity": "HIGH",
            "status": "RESOLVED", "assigned_investigator": "Andrew (SOC Operations)", "suspect_entity": "ATM Guard Rogue Reader",
            "description": "Card data copied at unmonitored ATM.", "action_taken": "ATM camera checked, card reissued."
        },
        {
            "ticket_number": "FRD-2025-HIST-105", "customer_id": 5, "customer_name": "Manish Aggarwal", "account_number": "ACT-5566-7788",
            "incident_type": "AnyDesk Remote Desktop Access Fraud", "amount_involved": 95000.0, "recovered_amount": 60000.0,
            "incident_date": datetime(2025, 4, 18, 9, 15), "reported_channel": "Customer Care", "severity": "CRITICAL",
            "status": "RESOLVED", "assigned_investigator": "Andrew (SOC Operations)", "suspect_entity": "Fake Support TeamViewer ID",
            "description": "Victim tricked into sharing device screen.", "action_taken": "NetBanking password reset; partial recovery."
        },
        # 2024 Multi-Year Historical Records
        {
            "ticket_number": "FRD-2024-HIST-201", "customer_id": 3, "customer_name": "Rohan Deshpande", "account_number": "ACT-3388-7711",
            "incident_type": "ATM Card Skimming & Cloned PIN Replay", "amount_involved": 50000.0, "recovered_amount": 50000.0,
            "incident_date": datetime(2024, 11, 5, 20, 10), "reported_channel": "ATM Terminal Alert", "severity": "HIGH",
            "status": "RESOLVED", "assigned_investigator": "Andrew (SOC Operations)", "suspect_entity": "Skimmer Unit MG Road",
            "description": "Magnetic strip skimmed at highway ATM.", "action_taken": "Card cancelled; insurance claim settled."
        },
        {
            "ticket_number": "FRD-2024-HIST-202", "customer_id": 4, "customer_name": "Ananya Sen", "account_number": "ACT-4455-6622",
            "incident_type": "Fake Airline Ticket Refund Helpline Scam", "amount_involved": 28000.0, "recovered_amount": 28000.0,
            "incident_date": datetime(2024, 9, 14, 13, 20), "reported_channel": "Helpdesk Call", "severity": "LOW",
            "status": "RESOLVED", "assigned_investigator": "Andrew (SOC Operations)", "suspect_entity": "Google Ads Fake Airline Number",
            "description": "Customer searched for airline support.", "action_taken": "Beneficiary bank returned funds."
        },
        {
            "ticket_number": "FRD-2024-HIST-203", "customer_id": 5, "customer_name": "Manish Aggarwal", "account_number": "ACT-5566-7788",
            "incident_type": "Stolen Cheque Cloned Signature Fraud", "amount_involved": 180000.0, "recovered_amount": 180000.0,
            "incident_date": datetime(2024, 7, 20, 15, 45), "reported_channel": "Clearing House Alert", "severity": "CRITICAL",
            "status": "RESOLVED", "assigned_investigator": "Andrew (SOC Operations)", "suspect_entity": "Forged Clearing Agent",
            "description": "Cheque intercepted in transit; signature forged.", "action_taken": "Cheque stopped at CTS clearing."
        },
        {
            "ticket_number": "FRD-2024-HIST-204", "customer_id": 1, "customer_name": "Arjun Singhal", "account_number": "ACT-1102-9901",
            "incident_type": "Credit Card Reward Points Redirection Scam", "amount_involved": 19500.0, "recovered_amount": 19500.0,
            "incident_date": datetime(2024, 4, 11, 17, 30), "reported_channel": "Online Banking Alert", "severity": "LOW",
            "status": "RESOLVED", "assigned_investigator": "Andrew (SOC Operations)", "suspect_entity": "RewardsPointsRedeem.com",
            "description": "Phishing website collected OTP.", "action_taken": "Voucher cancellation requested and granted."
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
