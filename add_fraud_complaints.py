#!/usr/bin/env python3
"""
================================================================================
Add 20 Fraud Complaints to PostgreSQL Database (bank_fraud_portal)
================================================================================
"""

import os
import sys
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pg8000.dbapi

load_dotenv(override=True)

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "")
DB_NAME = os.getenv("DB_NAME", "bank_fraud_portal")

# 20 New Curated Fraud Complaint Records
NEW_COMPLAINTS = [
    {
        "cust_name": "Arjun Singhal",
        "email": "arjun.singhal@delhitextiles.in",
        "phone": "+91 98110 54321",
        "city": "New Delhi",
        "state": "Delhi",
        "acc_num": "ACT-1102-9901",
        "acc_type": "SAVINGS",
        "ticket_num": "FRD-2026-9201",
        "incident_type": "UPI Payment QR Code Phishing",
        "amount": 42500.00,
        "recovered": 42500.00,
        "channel": "UPI App Dispute",
        "severity": "HIGH",
        "status": "RESOLVED",
        "investigator": "Pooja Deshmukh (SOC Analyst)",
        "ip_loc": "49.207.180.22 (Noida, India)",
        "suspect": "Fake OLX Seller (QR Collect Request)",
        "desc": "Customer received a malicious QR code disguised as payment receipt for used furniture sale. Scanning triggered an instant debit of ₹42,500.",
        "action": "Beneficiary UPI VPA blacklisted immediately; chargeback filed with NPCI and funds successfully recalled."
    },
    {
        "cust_name": "Kavita Krishnamurthy",
        "email": "kavita.k@bengalurubiopro.in",
        "phone": "+91 98450 78912",
        "city": "Bengaluru",
        "state": "Karnataka",
        "acc_num": "ACT-2244-8812",
        "acc_type": "CHECKING",
        "ticket_num": "FRD-2026-9202",
        "incident_type": "SIM Swap & NetBanking Hijacking",
        "amount": 185000.00,
        "recovered": 92500.00,
        "channel": "SOC Security Alert",
        "severity": "CRITICAL",
        "status": "FROZEN",
        "investigator": "Vikram Joshi (Resolution Specialist)",
        "ip_loc": "185.220.101.5 (Tor Exit Node)",
        "suspect": "Cloned eSIM Profile / Proxy Server",
        "desc": "Customer mobile SIM was deactivated without consent via unauthorized eSIM swap. Attackers initiated high-value NEFT transfers.",
        "action": "Account placed in FROZEN state; automated AutomationEdge BlockBankAccount workflow executed. Inter-bank lien marked on recipient bank."
    },
    {
        "cust_name": "Rohan Deshpande",
        "email": "rohan.deshpande@punelogistics.com",
        "phone": "+91 98220 33445",
        "city": "Pune",
        "state": "Maharashtra",
        "acc_num": "ACT-3388-7711",
        "acc_type": "BUSINESS",
        "ticket_num": "FRD-2026-9203",
        "incident_type": "Fake Electricity Bill SMS Scam",
        "amount": 14999.00,
        "recovered": 14999.00,
        "channel": "Customer Helpline",
        "severity": "MEDIUM",
        "status": "RESOLVED",
        "investigator": "Rajesh Nair (Fraud Team)",
        "ip_loc": "103.15.24.18 (Mumbai, India)",
        "suspect": "MSEDCL Impersonation Portal",
        "desc": "Customer received urgent SMS warning of electricity disconnection tonight. Clicking link prompted APK download which captured card details.",
        "action": "Debit card hotlisted instantly. Transaction reversed under Zero-Liability Fraud Policy."
    },
    {
        "cust_name": "Ananya Sen",
        "email": "ananya.sen@kolkatateas.in",
        "phone": "+91 98300 45678",
        "city": "Kolkata",
        "state": "West Bengal",
        "acc_num": "ACT-4455-6622",
        "acc_type": "SAVINGS",
        "ticket_num": "FRD-2026-9204",
        "incident_type": "Fake Work-From-Home Telegram Task Scam",
        "amount": 75000.00,
        "recovered": 0.00,
        "channel": "Internet Banking Portal",
        "severity": "HIGH",
        "status": "UNDER_INVESTIGATION",
        "investigator": "Shreya Deshmukh (Support Lead)",
        "ip_loc": "194.26.29.110 (Seychelles VPN)",
        "suspect": "Telegram Group @GlobalTasksHQ",
        "desc": "Victim was promised ₹3,000/day for reviewing hotel listings, lured into depositing ₹75,000 into tiered cryptocurrency escrow wallets.",
        "action": "Fraud incident registered with National Cyber Crime Reporting Portal (1930 Helpline). Destination crypto exchange alerted."
    },
    {
        "cust_name": "Manish Aggarwal",
        "email": "manish.aggarwal@chandigarhauto.in",
        "phone": "+91 98140 67890",
        "city": "Chandigarh",
        "state": "Punjab",
        "acc_num": "ACT-5566-7733",
        "acc_type": "BUSINESS",
        "ticket_num": "FRD-2026-9205",
        "incident_type": "Corporate Email Compromise (Vendor Invoice Spoof)",
        "amount": 340000.00,
        "recovered": 340000.00,
        "channel": "Relationship Manager Desk",
        "severity": "CRITICAL",
        "status": "RESOLVED",
        "investigator": "Vikram Joshi (Resolution Specialist)",
        "ip_loc": "198.51.100.42 (Frankfurt, Germany)",
        "suspect": "Domain Typosquatting (steelltd-in.com)",
        "desc": "Fraudster created lookalike domain resembling genuine raw material supplier and sent updated bank account details for RTGS payout.",
        "action": "RTGS transmission intercepted in transit via RBI Core Banking Gateway; full amount returned to customer."
    },
    {
        "cust_name": "Sunita Verma",
        "email": "sunita.verma@lucknowinfra.in",
        "phone": "+91 94150 12389",
        "city": "Lucknow",
        "state": "Uttar Pradesh",
        "acc_num": "ACT-6677-8844",
        "acc_type": "SAVINGS",
        "ticket_num": "FRD-2026-9206",
        "incident_type": "ATM Card Skimming & Cloned PIN Replay",
        "amount": 30000.00,
        "recovered": 30000.00,
        "channel": "ATM Surveillance Alert",
        "severity": "HIGH",
        "status": "RESOLVED",
        "investigator": "Pooja Bansal (Customer Support)",
        "ip_loc": "ATM Kiosk #LK-402, Hazratganj",
        "suspect": "Physical Skimmer Overlay Device",
        "desc": "Unauthorized ATM cash withdrawals performed at 3:00 AM using cloned magnetic stripe card while physical card was in customer possession.",
        "action": "ATM machine inspected by physical security team; card deactivated and fresh EMV Chip card dispatched."
    },
    {
        "cust_name": "Deepak Choudhury",
        "email": "deepak.c@guwahatilogistics.in",
        "phone": "+91 94350 99881",
        "city": "Guwahati",
        "state": "Assam",
        "acc_num": "ACT-7788-9955",
        "acc_type": "CHECKING",
        "ticket_num": "FRD-2026-9207",
        "incident_type": "Fake Bank KYC Update Phishing APK",
        "amount": 56000.00,
        "recovered": 28000.00,
        "channel": "Mobile Banking App",
        "severity": "HIGH",
        "status": "UNDER_INVESTIGATION",
        "investigator": "Rajesh Nair (Fraud Team)",
        "ip_loc": "103.220.14.88 (Patna, India)",
        "suspect": "Malicious App: ABCBank_KYC_Update.apk",
        "desc": "Customer received SMS stating account will be blocked within 24h unless KYC updated. Installed malicious APK that granted SMS read permissions.",
        "action": "NetBanking access revoked; device fingerprint blocklisted; partial ₹28,000 stopped before second beneficiary cash-out."
    },
    {
        "cust_name": "Farhan Qureshi",
        "email": "farhan.q@hyderabadleather.in",
        "phone": "+91 98490 22334",
        "city": "Hyderabad",
        "state": "Telangana",
        "acc_num": "ACT-8899-0066",
        "acc_type": "WEALTH_MANAGEMENT",
        "ticket_num": "FRD-2026-9208",
        "incident_type": "Fake Stock Trading App IPO Allocation Scam",
        "amount": 520000.00,
        "recovered": 0.00,
        "channel": "Branch Walk-in",
        "severity": "CRITICAL",
        "status": "ESCALATED",
        "investigator": "Vikram Joshi (Resolution Specialist)",
        "ip_loc": "45.142.214.18 (Cyprus Proxy)",
        "suspect": "Institutional Wealth Club App (Sideloaded)",
        "desc": "Customer transferred ₹5.2 Lakhs into mule accounts for pre-IPO allotments via a fake trading platform displaying simulated profits.",
        "action": "Police FIR filed under IT Act 66D; mule bank accounts identified and reported to LEA / Financial Intelligence Unit (FIU-IND)."
    },
    {
        "cust_name": "Geeta Sundaram",
        "email": "geeta.sundaram@chennaiconsult.in",
        "phone": "+91 98401 66778",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "acc_num": "ACT-9900-1177",
        "acc_type": "SAVINGS",
        "ticket_num": "FRD-2026-9209",
        "incident_type": "Unauthorized International E-Commerce CNP Transactions",
        "amount": 68400.00,
        "recovered": 68400.00,
        "channel": "SMS Fraud Alert Response",
        "severity": "HIGH",
        "status": "RESOLVED",
        "investigator": "Pooja Deshmukh (SOC Analyst)",
        "ip_loc": "195.181.162.20 (London, UK)",
        "suspect": "Overseas Merchant: LUXURY_GOODS_UK",
        "desc": "Series of 4 Card-Not-Present transactions processed in GBP without OTP prompt on international gateway.",
        "action": "International card usage disabled; Visa Chargeback Dispute raised; temporary credit posted to customer account."
    },
    {
        "cust_name": "Tariq Mansoori",
        "email": "tariq.m@bhopalhandicrafts.in",
        "phone": "+91 94250 88990",
        "city": "Bhopal",
        "state": "Madhya Pradesh",
        "acc_num": "ACT-1011-2288",
        "acc_type": "SAVINGS",
        "ticket_num": "FRD-2026-9210",
        "incident_type": "Credit Card Reward Points Redirection Scam",
        "amount": 21500.00,
        "recovered": 21500.00,
        "channel": "Website Help Form",
        "severity": "MEDIUM",
        "status": "RESOLVED",
        "investigator": "Pooja Bansal (Customer Support)",
        "ip_loc": "103.44.112.5 (Indore, India)",
        "suspect": "Spoofed Portal: abc-rewardpoints-claim.net",
        "desc": "Customer received SMS promising ₹8,500 cash back from expiring reward points. Entering CVV and OTP resulted in wallet recharge.",
        "action": "Wallet merchant notified within 15 mins; recharge reversed and ₹21,500 credited back."
    },
    {
        "cust_name": "Siddharth Rao",
        "email": "siddharth.rao@visakhaseafoods.in",
        "phone": "+91 98480 33441",
        "city": "Visakhapatnam",
        "state": "Andhra Pradesh",
        "acc_num": "ACT-1122-3399",
        "acc_type": "BUSINESS",
        "ticket_num": "FRD-2026-9211",
        "incident_type": "Digital Arrest Extortion (Fake CBI / Police Video Call)",
        "amount": 250000.00,
        "recovered": 175000.00,
        "channel": "SOC Security Alert",
        "severity": "CRITICAL",
        "status": "FROZEN",
        "investigator": "Shreya Deshmukh (Support Lead)",
        "ip_loc": "Skype Video ID: CyberCrime_Cell_Gov",
        "suspect": "Impersonators posing as Mumbai Cyber Cell",
        "desc": "Customer coerced on 6-hour video call under threat of arrest for alleged narcotic parcel sent in their name, transferring ₹2.5 Lakhs.",
        "action": "Immediate freeze request sent to receiving banks; ₹1.75 Lakhs locked in recipient accounts before withdrawal."
    },
    {
        "cust_name": "Nidhi Agarwal",
        "email": "nidhi.agarwal@jaipurcrafts.in",
        "phone": "+91 94140 55667",
        "city": "Jaipur",
        "state": "Rajasthan",
        "acc_num": "ACT-1233-4400",
        "acc_type": "SAVINGS",
        "ticket_num": "FRD-2026-9212",
        "incident_type": "AnyDesk Remote Desktop Access Fraud",
        "amount": 89000.00,
        "recovered": 89000.00,
        "channel": "Customer Helpline",
        "severity": "HIGH",
        "status": "RESOLVED",
        "investigator": "Rajesh Nair (Fraud Team)",
        "ip_loc": "AnyDesk Session ID: 941-205-118",
        "suspect": "Fake Customer Support Representative",
        "desc": "Fraudster called pretending to resolve pending broadband refund and instructed customer to install AnyDesk on mobile.",
        "action": "NetBanking locked within 4 minutes; pending IMPS transactions aborted; customer device guided through remote tool uninstall."
    },
    {
        "cust_name": "Harishankar Pandey",
        "email": "harishankar.p@varanasisilk.in",
        "phone": "+91 94500 11223",
        "city": "Varanasi",
        "state": "Uttar Pradesh",
        "acc_num": "ACT-1344-5511",
        "acc_type": "CHECKING",
        "ticket_num": "FRD-2026-9213",
        "incident_type": "Fake Instant Personal Loan App Data Extortion",
        "amount": 35000.00,
        "recovered": 0.00,
        "channel": "Internet Banking Portal",
        "severity": "MEDIUM",
        "status": "UNDER_INVESTIGATION",
        "investigator": "Pooja Bansal (Customer Support)",
        "ip_loc": "185.190.140.2 (Netherlands Hosting)",
        "suspect": "Instant Rupee Credit App (Third-party APK)",
        "desc": "Customer downloaded unverified loan app which accessed contacts list and demanded extortion payments despite 0 loan disbursement.",
        "action": "Case documented for cyber cell; security advisory issued to customer to format mobile device."
    },
    {
        "cust_name": "Swati Deshpande",
        "email": "swati.deshpande@nashikwinery.in",
        "phone": "+91 98230 44556",
        "city": "Nashik",
        "state": "Maharashtra",
        "acc_num": "ACT-1455-6622",
        "acc_type": "WEALTH_MANAGEMENT",
        "ticket_num": "FRD-2026-9214",
        "incident_type": "Stolen Cheque Cloned Signature Fraud",
        "amount": 160000.00,
        "recovered": 160000.00,
        "channel": "Branch Clearing Desk",
        "severity": "HIGH",
        "status": "RESOLVED",
        "investigator": "Vikram Joshi (Resolution Specialist)",
        "ip_loc": "Clearing House CTS-2010 Mumbai",
        "suspect": "Intercepted Courier Cheque Leaf",
        "desc": "High-value physical bearer cheque presented at third-party branch with digitally altered payee name and forged signature.",
        "action": "Cheque Clearing stopped by Positive Pay System validation mismatch; returned with memo 'Signature Differs'."
    },
    {
        "cust_name": "Gaurav Malhotra",
        "email": "gaurav.malhotra@indorepharma.in",
        "phone": "+91 98260 77889",
        "city": "Indore",
        "state": "Madhya Pradesh",
        "acc_num": "ACT-1566-7733",
        "acc_type": "BUSINESS",
        "ticket_num": "FRD-2026-9215",
        "incident_type": "Multiple Micro Unauthorized IMPS Transfers",
        "amount": 49800.00,
        "recovered": 49800.00,
        "channel": "Automated Transaction Rule Engine",
        "severity": "HIGH",
        "status": "RESOLVED",
        "investigator": "Pooja Deshmukh (SOC Analyst)",
        "ip_loc": "103.111.20.9 (Kolkata, India)",
        "suspect": "Automated Scripted IMPS Bot",
        "desc": "10 consecutive transactions of ₹4,980 triggered within 3 minutes targeting different beneficiary accounts across banks.",
        "action": "Automated Velocity Filter triggered account freeze; full amount recalled before end-of-day settlement."
    },
    {
        "cust_name": "Ayesha Siddiqui",
        "email": "ayesha.s@patnatech.in",
        "phone": "+91 94310 22334",
        "city": "Patna",
        "state": "Bihar",
        "acc_num": "ACT-1677-8844",
        "acc_type": "SAVINGS",
        "ticket_num": "FRD-2026-9216",
        "incident_type": "Fake Airline Ticket Refund Helpline Scam",
        "amount": 18200.00,
        "recovered": 18200.00,
        "channel": "Customer Helpline",
        "severity": "LOW",
        "status": "RESOLVED",
        "investigator": "Shreya Deshmukh (Support Lead)",
        "ip_loc": "Search Engine Sponsored Ad URL",
        "suspect": "Fake Google Listing: Indigo Customer Care",
        "desc": "Customer searched for airline support and dialed a sponsored fake toll-free number which requested ₹10 test refund fee via Google Pay.",
        "action": "Complaint escalated to UPI aggregator; ₹18,200 refunded in full to customer savings account."
    },
    {
        "cust_name": "Rameshwar Kulkarni",
        "email": "rameshwar.k@aurangabadauto.in",
        "phone": "+91 98225 66778",
        "city": "Chhatrapati Sambhajinagar",
        "state": "Maharashtra",
        "acc_num": "ACT-1788-9955",
        "acc_type": "CHECKING",
        "ticket_num": "FRD-2026-9217",
        "incident_type": "Fake Part-time Job WhatsApp Review Scam",
        "amount": 62000.00,
        "recovered": 0.00,
        "channel": "Internet Banking Portal",
        "severity": "HIGH",
        "status": "UNDER_INVESTIGATION",
        "investigator": "Rajesh Nair (Fraud Team)",
        "ip_loc": "104.28.210.15 (Cloudflare Proxy)",
        "suspect": "International Number +62 838-2910-331",
        "desc": "Victim invested ₹62,000 across 3 days after initial ₹500 profit payout; withdrawal was blocked requiring additional ₹50,000 'tax'.",
        "action": "Detailed dossier with UPI reference IDs shared with Cyber Police Station."
    },
    {
        "cust_name": "Sneha Mukherjee",
        "email": "sneha.m@siliguriagro.in",
        "phone": "+91 94340 88991",
        "city": "Siliguri",
        "state": "West Bengal",
        "acc_num": "ACT-1899-0066",
        "acc_type": "SAVINGS",
        "ticket_num": "FRD-2026-9218",
        "incident_type": "Debit Card Skimming at Fuel Pump POS Terminal",
        "amount": 27500.00,
        "recovered": 27500.00,
        "channel": "SMS Fraud Alert Response",
        "severity": "MEDIUM",
        "status": "RESOLVED",
        "investigator": "Pooja Bansal (Customer Support)",
        "ip_loc": "Highway Petrol Pump POS Terminal #3",
        "suspect": "Compromised POS Firmware Device",
        "desc": "Magnetic data skimmed during highway petrol station transaction; international POS transactions attempted 48 hours later in Dubai.",
        "action": "Card permanently blocked; replacement EMV chip card issued with zero liability for customer."
    },
    {
        "cust_name": "Manoj Tiwari",
        "email": "manoj.tiwari@ranchiminerals.in",
        "phone": "+91 94311 44556",
        "city": "Ranchi",
        "state": "Jharkhand",
        "acc_num": "ACT-1900-1177",
        "acc_type": "BUSINESS",
        "ticket_num": "FRD-2026-9219",
        "incident_type": "Forged Board Resolution & Unauthorized Beneficiary Addition",
        "amount": 450000.00,
        "recovered": 450000.00,
        "channel": "Corporate NetBanking Audit",
        "severity": "CRITICAL",
        "status": "RESOLVED",
        "investigator": "Vikram Joshi (Resolution Specialist)",
        "ip_loc": "Corporate Portal Gateway (Mumbai)",
        "suspect": "Compromised Corporate Signatory Token",
        "desc": "Disgruntled ex-employee attempted to add external vendor beneficiary using compromised secondary digital signature certificate.",
        "action": "Dual-control corporate approval blocked transaction; DSC certificates revoked and corporate security audit completed."
    },
    {
        "cust_name": "Pooja Hegde",
        "email": "pooja.hegde@mangaloreshipping.in",
        "phone": "+91 98455 11229",
        "city": "Mangaluru",
        "state": "Karnataka",
        "acc_num": "ACT-2011-2288",
        "acc_type": "WEALTH_MANAGEMENT",
        "ticket_num": "FRD-2026-9220",
        "incident_type": "Cryptocurrency Investment WhatsApp Pump & Dump",
        "amount": 310000.00,
        "recovered": 155000.00,
        "channel": "Customer Relationship Alert",
        "severity": "CRITICAL",
        "status": "FROZEN",
        "investigator": "Shreya Deshmukh (Support Lead)",
        "ip_loc": "185.244.25.10 (Hong Kong VPN)",
        "suspect": "VIP Crypto Signals Telegram Bot",
        "desc": "Customer convinced to transfer funds to third-party merchant for staking tokens on fake DEX platform.",
        "action": "Account temporarily frozen to prevent remaining ₹1.55 Lakh balance dissipation; AutomationEdge freeze workflow dispatched."
    }
]

def insert_20_fraud_complaints():
    print(f"[*] Connecting to PostgreSQL at {DB_HOST}:{DB_PORT} / {DB_NAME}...")

    conn = None
    passwords_to_try = [DB_PASS, "postgres", "admin", "Password@123", "root", ""]
    for pwd in passwords_to_try:
        try:
            conn = pg8000.dbapi.connect(
                user=DB_USER,
                password=pwd,
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME
            )
            break
        except Exception:
            continue

    if not conn:
        print(f"[!] Error: Could not connect to PostgreSQL database '{DB_NAME}' on {DB_HOST}:{DB_PORT}.")
        sys.exit(1)

    cursor = conn.cursor()

    # Get initial count
    cursor.execute("SELECT COUNT(*) FROM fraud_tickets;")
    initial_count = cursor.fetchone()[0]
    print(f"[*] Current fraud complaints in database: {initial_count}")

    inserted = 0
    skipped = 0

    base_date = datetime.now() - timedelta(days=20)

    for i, c in enumerate(NEW_COMPLAINTS):
        # 1. Insert or get Customer
        cust_code = f"CUST-803{i+1:02d}"
        cursor.execute("SELECT customer_id FROM customers WHERE email = %s OR customer_code = %s;", (c["email"], cust_code))
        row = cursor.fetchone()
        if row:
            customer_id = row[0]
        else:
            cursor.execute("""
                INSERT INTO customers (
                    customer_code, customer_name, full_name, email, phone, 
                    address, city, state, country, kyc_status, risk_tier, account_count,
                    username, password_hash, plain_password
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, 'India', 'VERIFIED', %s, 1,
                    %s, '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', 'Cust@123'
                ) RETURNING customer_id;
            """, (
                cust_code, c["cust_name"], c["cust_name"], c["email"], c["phone"],
                f"Suite {i*10 + 12}, Central Avenue", c["city"], c["state"], c["severity"],
                f"cust_{cust_code.lower()}"
            ))
            customer_id = cursor.fetchone()[0]

        # 2. Insert or get Account
        cursor.execute("SELECT account_id FROM customer_accounts WHERE account_number = %s;", (c["acc_num"],))
        acc_row = cursor.fetchone()
        if not acc_row:
            cursor.execute("""
                INSERT INTO customer_accounts (
                    customer_id, customer_name, account_number, account_type,
                    balance, currency, status, branch, opened_date
                ) VALUES (
                    %s, %s, %s, %s, %s, 'INR', %s, %s, %s
                );
            """, (
                customer_id, c["cust_name"], c["acc_num"], c["acc_type"],
                float(c["amount"] * 2.5),
                "FROZEN" if c["status"] == "FROZEN" else "ACTIVE",
                f"{c['city']} Central Branch",
                (datetime.now() - timedelta(days=random.randint(180, 720))).strftime("%Y-%m-%d")
            ))

        # 3. Check if Ticket already exists
        cursor.execute("SELECT ticket_id FROM fraud_tickets WHERE ticket_number = %s;", (c["ticket_num"],))
        if cursor.fetchone():
            skipped += 1
            continue

        # Calculate incident date
        incident_dt = (base_date + timedelta(days=i, hours=random.randint(8, 20), minutes=random.randint(10, 50))).strftime("%Y-%m-%d %H:%M:%S")

        # 4. Insert Fraud Ticket
        cursor.execute("""
            INSERT INTO fraud_tickets (
                ticket_number, customer_id, customer_name, account_number,
                incident_type, amount_involved, recovered_amount, incident_date,
                reported_channel, severity, status, assigned_investigator,
                flagged_ip_or_location, suspect_entity, description,
                action_taken, resolution_notes, idempotency_key
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s
            );
        """, (
            c["ticket_num"], customer_id, c["cust_name"], c["acc_num"],
            c["incident_type"], c["amount"], c["recovered"], incident_dt,
            c["channel"], c["severity"], c["status"], c["investigator"],
            c["ip_loc"], c["suspect"], c["desc"],
            c["action"], f"Audit reference generated on {incident_dt}",
            f"IDEM-AUTO-{c['ticket_num']}"
        ))

        # 5. Insert corresponding transaction record
        cursor.execute("""
            INSERT INTO transactions (
                txn_reference, customer_id, customer_name, account_number,
                amount, txn_type, merchant_or_recipient, channel,
                ip_address, geo_location, is_fraud_flagged, fraud_risk_score,
                status, txn_time
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, TRUE, %s,
                'FLAGGED', %s
            );
        """, (
            f"TXN-2026-{random.randint(100000, 999999)}", customer_id, c["cust_name"], c["acc_num"],
            c["amount"], "DEBIT", c["suspect"], c["channel"],
            c["ip_loc"].split(" ")[0], c["city"],
            95 if c["severity"] == "CRITICAL" else (75 if c["severity"] == "HIGH" else 50),
            incident_dt
        ))

        inserted += 1

    conn.commit()

    # Get final count
    cursor.execute("SELECT COUNT(*) FROM fraud_tickets;")
    final_count = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    print(f"\n[+] SUCCESS: Added {inserted} new fraud complaints! (Skipped existing: {skipped})")
    print(f"[+] Total fraud complaints in database now: {final_count}")

if __name__ == "__main__":
    insert_20_fraud_complaints()
