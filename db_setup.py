"""
Dummy Bank Portal - PostgreSQL Database Setup & Data Seeder
Creates the database `bank_fraud_portal` in PostgreSQL with 25 Indian customer fraud cases.
"""

import pg8000.dbapi
import sys
from datetime import datetime

from config import DB_HOST, DB_PORT, DB_USER, DB_PASS, DB_NAME
TARGET_DB = DB_NAME

CUSTOMERS_DATA = [
    {
        "code": "CUST-80219",
        "name": "Rajesh Sharma",
        "email": "rajesh.sharma@mumbaitech.in",
        "phone": "+91 98201 44521",
        "address": "42 Nariman Point, Marine Drive",
        "city": "Mumbai",
        "state": "Maharashtra",
        "risk_tier": "CRITICAL",
        "account_num": "ACT-4091-8821",
        "acc_type": "BUSINESS",
        "balance": 348250.00,
        "branch": "Mumbai Nariman Point Branch",
        "ticket": {
            "ticket_num": "FRD-2026-9081",
            "type": "Unauthorized Bank Transfer",
            "amount": 125000.00,
            "recovered": 125000.00,
            "date": "2026-09-15 14:22:00",
            "channel": "Online Banking Alert",
            "severity": "CRITICAL",
            "status": "FROZEN",
            "investigator": "Shreya Deshmukh (Support Lead)",
            "ip_loc": "185.220.101.44 (Unknown IP)",
            "suspect": "Unverified Beneficiary Account",
            "desc": "Customer noticed an unauthorized online transfer request of ₹1,25,000 sent to an unknown bank account.",
            "action": "Bank immediately recalled the transfer and temporarily blocked the account to safeguard funds."
        }
    },
    {
        "code": "CUST-80220",
        "name": "Priya Patel",
        "email": "priya.patel@gujarattextiles.co.in",
        "phone": "+91 98980 12345",
        "address": "12 SG Highway, Bodakdev",
        "city": "Ahmedabad",
        "state": "Gujarat",
        "risk_tier": "HIGH",
        "account_num": "ACT-7712-4490",
        "acc_type": "WEALTH_MANAGEMENT",
        "balance": 892100.00,
        "branch": "Ahmedabad SG Highway Branch",
        "ticket": {
            "ticket_num": "FRD-2026-9082",
            "type": "SIM Card Swap & Fake OTP Scam",
            "amount": 48500.00,
            "recovered": 0.00,
            "date": "2026-09-14 09:15:00",
            "channel": "Customer Helpline",
            "severity": "HIGH",
            "status": "UNDER_INVESTIGATION",
            "investigator": "Rajesh Nair (Fraud Team)",
            "ip_loc": "104.28.19.88 (Mobile Proxy)",
            "suspect": "Unverified Wallet Service",
            "desc": "Customer experienced sudden mobile signal loss and found two unauthorized online transfer OTP requests.",
            "action": "NetBanking access secured and SIM verification initiated."
        }
    },
    {
        "code": "CUST-80221",
        "name": "Vikramaditya Singhania",
        "email": "vikram.singhania@singhania-law.in",
        "phone": "+91 98205 67890",
        "address": "15 Fort Chambers, Flora Fountain",
        "city": "Mumbai",
        "state": "Maharashtra",
        "risk_tier": "MEDIUM",
        "account_num": "ACT-3381-9920",
        "acc_type": "CHECKING",
        "balance": 42150.00,
        "branch": "Mumbai Fort Main Branch",
        "ticket": {
            "ticket_num": "FRD-2026-9083",
            "type": "Fake Email / Fake Bill Scam",
            "amount": 18400.00,
            "recovered": 12000.00,
            "date": "2026-09-12 16:45:00",
            "channel": "Website Help Form",
            "severity": "MEDIUM",
            "status": "RESOLVED",
            "investigator": "Pooja Bansal (Customer Support)",
            "ip_loc": "194.38.20.12",
            "suspect": "Spoofed Billing Email",
            "desc": "Customer received a fake invoice resembling their regular vendor with modified bank account details.",
            "action": "₹12,000 reversed and refunded back to customer account."
        }
    },
    {
        "code": "CUST-80222",
        "name": "Ananya Iyer",
        "email": "ananya.iyer@bangaloredesign.in",
        "phone": "+91 99001 88223",
        "address": "88 100ft Road, Indiranagar",
        "city": "Bengaluru",
        "state": "Karnataka",
        "risk_tier": "CRITICAL",
        "account_num": "ACT-9901-2211",
        "acc_type": "CREDIT_CARD",
        "balance": 18900.00,
        "branch": "Bengaluru Indiranagar Branch",
        "ticket": {
            "ticket_num": "FRD-2026-9084",
            "type": "ATM / Card Cloning Scam",
            "amount": 27300.00,
            "recovered": 27300.00,
            "date": "2026-09-16 21:05:00",
            "channel": "Mobile Banking",
            "severity": "CRITICAL",
            "status": "RESOLVED",
            "investigator": "Shreya Deshmukh (Support Lead)",
            "ip_loc": "Card POS Terminal #4401",
            "suspect": "Cloned Card Swipe",
            "desc": "Card was physically in customer's wallet in Bengaluru while 2 consecutive transactions occurred in an overseas store.",
            "action": "Card permanently blocked; Zero-liability claim processed; Full amount refunded."
        }
    },
    {
        "code": "CUST-80223",
        "name": "Amit Verma",
        "email": "amit.verma@delhicorporate.in",
        "phone": "+91 98110 33445",
        "address": "15 Barakhamba Road, Connaught Place",
        "city": "Delhi",
        "state": "Delhi",
        "risk_tier": "HIGH",
        "account_num": "ACT-5510-1188",
        "acc_type": "BUSINESS",
        "balance": 612400.00,
        "branch": "Connaught Place Branch",
        "ticket": {
            "ticket_num": "FRD-2026-9085",
            "type": "Unauthorized Salary Deduction Scam",
            "amount": 64200.00,
            "recovered": 48000.00,
            "date": "2026-09-13 08:30:00",
            "channel": "Branch Visit",
            "severity": "HIGH",
            "status": "UNDER_INVESTIGATION",
            "investigator": "Vikram Joshi (Resolution Specialist)",
            "ip_loc": "45.154.255.80",
            "suspect": "Unverified Beneficiary List",
            "desc": "Staff payroll direct deposit accounts were unauthorizedly modified before monthly disbursement.",
            "action": "Disbursement halted; 11 accounts secured; Funds in process of recovery."
        }
    },
    {
        "code": "CUST-80224",
        "name": "Dr. Neha Kulkarni",
        "email": "neha.kulkarni@puneresearch.ac.in",
        "phone": "+91 98220 99881",
        "address": "300 FC Road, Shivajinagar",
        "city": "Pune",
        "state": "Maharashtra",
        "risk_tier": "CRITICAL",
        "account_num": "ACT-1099-3401",
        "acc_type": "SAVINGS",
        "balance": 520000.00,
        "branch": "Pune FC Road Branch",
        "ticket": {
            "ticket_num": "FRD-2026-9086",
            "type": "Fake Phone Call Scam",
            "amount": 95000.00,
            "recovered": 0.00,
            "date": "2026-09-11 11:10:00",
            "channel": "Customer Helpline",
            "severity": "CRITICAL",
            "status": "ESCALATED",
            "investigator": "Shreya Deshmukh (Support Lead)",
            "ip_loc": "VoIP Gateway",
            "suspect": "Fake Insurance Agent",
            "desc": "Customer received a spoofed phone call posing as senior bank manager demanding urgent transfer for policy clearance.",
            "action": "Report escalated to Cyber Crime Cell; Recipient account freeze notice issued."
        }
    },
    {
        "code": "CUST-80225",
        "name": "Suresh Reddy",
        "email": "suresh.reddy@hyderabadagri.in",
        "phone": "+91 98490 77665",
        "address": "400 Road No 10, Banjara Hills",
        "city": "Hyderabad",
        "state": "Telangana",
        "risk_tier": "MEDIUM",
        "account_num": "ACT-2244-6677",
        "acc_type": "CHECKING",
        "balance": 78900.00,
        "branch": "Banjara Hills Branch",
        "ticket": {
            "ticket_num": "FRD-2026-9087",
            "type": "Fake / Altered Cheque Deposit",
            "amount": 14250.00,
            "recovered": 14250.00,
            "date": "2026-09-10 15:20:00",
            "channel": "Online Banking Alert",
            "severity": "MEDIUM",
            "status": "RESOLVED",
            "investigator": "Pooja Bansal (Customer Support)",
            "ip_loc": "Clearing House Terminal",
            "suspect": "Chemical Erasure Altered Cheque",
            "desc": "Cheque issued to vendor intercepted, payee name chemically washed and amount altered.",
            "action": "Original cheque retrieved; Payee verified; Cleared amount returned to customer."
        }
    },
    {
        "code": "CUST-80226",
        "name": "Pooja Mehta",
        "email": "pooja.mehta@surattextiles.in",
        "phone": "+91 98790 55432",
        "address": "210 Ring Road, Varachha",
        "city": "Surat",
        "state": "Gujarat",
        "risk_tier": "HIGH",
        "account_num": "ACT-6632-1109",
        "acc_type": "BUSINESS",
        "balance": 182300.00,
        "branch": "Surat Ring Road Branch",
        "ticket": {
            "ticket_num": "FRD-2026-9088",
            "type": "Fake Login Link / Phishing Scam",
            "amount": 38900.00,
            "recovered": 38900.00,
            "date": "2026-09-16 10:40:00",
            "channel": "Online Banking Alert",
            "severity": "HIGH",
            "status": "RESOLVED",
            "investigator": "Shreya Deshmukh (Support Lead)",
            "ip_loc": "91.240.118.5 (Proxy Server)",
            "suspect": "Fake Banking Website Link",
            "desc": "Customer entered credentials into a lookalike fake bank website received over WhatsApp.",
            "action": "NetBanking password invalidated; Two-factor authentication reset."
        }
    },
    {
        "code": "CUST-80227",
        "name": "Rohan Gupta",
        "email": "rohan.gupta@noidafintech.in",
        "phone": "+91 98180 66778",
        "address": "Sector 62, Electronic City",
        "city": "Noida",
        "state": "Uttar Pradesh",
        "risk_tier": "CRITICAL",
        "account_num": "ACT-8841-0023",
        "acc_type": "WEALTH_MANAGEMENT",
        "balance": 1450000.00,
        "branch": "Noida Sector 62 Branch",
        "ticket": {
            "ticket_num": "FRD-2026-9089",
            "type": "Unauthorized Overseas Transfer",
            "amount": 250000.00,
            "recovered": 250000.00,
            "date": "2026-09-17 04:12:00",
            "channel": "Online Banking Alert",
            "severity": "CRITICAL",
            "status": "FROZEN",
            "investigator": "Shreya Deshmukh (Support Lead)",
            "ip_loc": "178.62.204.18",
            "suspect": "Unregistered Foreign Portal",
            "desc": "Automatic safety system stopped an unauthorized ₹2,50,000 transfer instruction.",
            "action": "Account temporarily blocked; Customer verified in person."
        }
    },
    {
        "code": "CUST-80228",
        "name": "Sneha Nair",
        "email": "sneha.nair@cochinspices.in",
        "phone": "+91 94470 11223",
        "address": "14 MG Road, Ernakulam",
        "city": "Kochi",
        "state": "Kerala",
        "risk_tier": "MEDIUM",
        "account_num": "ACT-9012-7734",
        "acc_type": "CHECKING",
        "balance": 62400.00,
        "branch": "Kochi MG Road Branch",
        "ticket": {
            "ticket_num": "FRD-2026-9090",
            "type": "ATM Skimming & Unauthorized Cash Withdrawal",
            "amount": 6200.00,
            "recovered": 6200.00,
            "date": "2026-09-09 23:18:00",
            "channel": "Mobile Banking",
            "severity": "MEDIUM",
            "status": "RESOLVED",
            "investigator": "Pooja Bansal (Customer Support)",
            "ip_loc": "ATM-Kochi-Airport-Terminal",
            "suspect": "ATM Hardware Skimmer Device",
            "desc": "3 consecutive unauthorized cash withdrawals of ₹2,000 each at an airport ATM.",
            "action": "ATM machine inspected and device removed; ₹6,200 reimbursed to customer."
        }
    },
    {
        "code": "CUST-80229",
        "name": "Rahul Deshmukh",
        "email": "rahul.deshmukh@nagpurbusiness.in",
        "phone": "+91 98230 44556",
        "address": "50 Civil Lines, Palm Road",
        "city": "Nagpur",
        "state": "Maharashtra",
        "risk_tier": "HIGH",
        "account_num": "ACT-3190-8844",
        "acc_type": "BUSINESS",
        "balance": 940000.00,
        "branch": "Nagpur Civil Lines Branch",
        "ticket": {
            "ticket_num": "FRD-2026-9091",
            "type": "Compromised Email & Fake Payment Instructions",
            "amount": 185000.00,
            "recovered": 140000.00,
            "date": "2026-09-08 13:00:00",
            "channel": "Branch Visit",
            "severity": "HIGH",
            "status": "UNDER_INVESTIGATION",
            "investigator": "Vikram Joshi (Resolution Specialist)",
            "ip_loc": "198.51.100.22",
            "suspect": "Spoofed Supplier Account",
            "desc": "Company email account hijacked; scammers asked for raw material payment to a fake bank account.",
            "action": "₹1,40,000 intercepted and saved; Remaining ₹45,000 under recovery."
        }
    },
    {
        "code": "CUST-80230",
        "name": "Sunita Rao",
        "email": "sunita.rao@koramangala-invest.in",
        "phone": "+91 98450 99001",
        "address": "Level 4, Koramangala 5th Block",
        "city": "Bengaluru",
        "state": "Karnataka",
        "risk_tier": "CRITICAL",
        "account_num": "ACT-7788-9900",
        "acc_type": "WEALTH_MANAGEMENT",
        "balance": 2150000.00,
        "branch": "Koramangala Premier Branch",
        "ticket": {
            "ticket_num": "FRD-2026-9092",
            "type": "Online Crypto Wallet Scam",
            "amount": 310000.00,
            "recovered": 0.00,
            "date": "2026-09-07 19:45:00",
            "channel": "Website Help Form",
            "severity": "CRITICAL",
            "status": "ESCALATED",
            "investigator": "Shreya Deshmukh (Support Lead)",
            "ip_loc": "Fake Crypto Portal",
            "suspect": "Fraudulent Crypto Scheme",
            "desc": "Customer transferred funds to a fraudulent high-return crypto trading app that blocked withdrawals.",
            "action": "Complaint registered with Cyber Police cell; Beneficiary details submitted."
        }
    },
    {
        "code": "CUST-80231",
        "name": "Manoj Aggarwal",
        "email": "manoj.aggarwal@chandigarhretail.in",
        "phone": "+91 98140 12890",
        "address": "12 Sector 17 Plaza",
        "city": "Chandigarh",
        "state": "Chandigarh",
        "risk_tier": "MEDIUM",
        "account_num": "ACT-5502-3311",
        "acc_type": "CHECKING",
        "balance": 34100.00,
        "branch": "Chandigarh Sector 17 Branch",
        "ticket": {
            "ticket_num": "FRD-2026-9093",
            "type": "Fake Bank SMS Alert Scam",
            "amount": 4900.00,
            "recovered": 4900.00,
            "date": "2026-09-06 17:15:00",
            "channel": "Mobile Banking",
            "severity": "MEDIUM",
            "status": "RESOLVED",
            "investigator": "Pooja Bansal (Customer Support)",
            "ip_loc": "SMS Header 'ALERT-BANK'",
            "suspect": "Fake SMS Web Link",
            "desc": "Customer received SMS stating debit card was blocked, clicked link and entered card details.",
            "action": "Card blocked and replaced immediately; Transaction disputed and refunded."
        }
    },
    {
        "code": "CUST-80232",
        "name": "Deepa Sundaram",
        "email": "deepa.sundaram@chennailegal.in",
        "phone": "+91 98400 77112",
        "address": "800 2nd Avenue, Anna Nagar",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "risk_tier": "HIGH",
        "account_num": "ACT-6619-0012",
        "acc_type": "CHECKING",
        "balance": 115000.00,
        "branch": "Chennai Anna Nagar Branch",
        "ticket": {
            "ticket_num": "FRD-2026-9094",
            "type": "Property Purchase Advance Payment Scam",
            "amount": 75000.00,
            "recovered": 75000.00,
            "date": "2026-09-05 14:00:00",
            "channel": "Branch Visit",
            "severity": "CRITICAL",
            "status": "RESOLVED",
            "investigator": "Shreya Deshmukh (Support Lead)",
            "ip_loc": "Fake Builder Email Address",
            "suspect": "Spoofed Builder Account",
            "desc": "Customer received fake bank account details for property booking advance payment.",
            "action": "Transfer stopped before settlement; Full ₹75,000 preserved in account."
        }
    },
    {
        "code": "CUST-80233",
        "name": "Kunal Malhotra",
        "email": "kunal.malhotra@gurugramtech.in",
        "phone": "+91 98100 01923",
        "address": "DLF Cyber City Tower B",
        "city": "Gurugram",
        "state": "Haryana",
        "risk_tier": "HIGH",
        "account_num": "ACT-8822-4411",
        "acc_type": "SAVINGS",
        "balance": 410000.00,
        "branch": "Cyber City Branch",
        "ticket": {
            "ticket_num": "FRD-2026-9095",
            "type": "Malicious App Installed on Phone",
            "amount": 22000.00,
            "recovered": 18000.00,
            "date": "2026-09-04 11:20:00",
            "channel": "Online Banking Alert",
            "severity": "HIGH",
            "status": "UNDER_INVESTIGATION",
            "investigator": "Vikram Joshi (Resolution Specialist)",
            "ip_loc": "193.106.191.24",
            "suspect": "Malicious App APK",
            "desc": "Customer accidentally installed an unauthorized utility app that read SMS notifications.",
            "action": "Mobile banking app deregistered from infected phone; ₹18,000 recovered."
        }
    },
    {
        "code": "CUST-80234",
        "name": "Shalini Menon",
        "email": "shalini.menon@keralatrust.in",
        "phone": "+91 94471 23456",
        "address": "44 Palayam Main Road",
        "city": "Thiruvananthapuram",
        "state": "Kerala",
        "risk_tier": "LOW",
        "account_num": "ACT-3311-9988",
        "acc_type": "CHECKING",
        "balance": 54000.00,
        "branch": "Palayam Branch",
        "ticket": {
            "ticket_num": "FRD-2026-9096",
            "type": "Unwanted Recurring Online Charges",
            "amount": 1280.00,
            "recovered": 1280.00,
            "date": "2026-09-03 09:00:00",
            "channel": "Mobile Banking",
            "severity": "LOW",
            "status": "RESOLVED",
            "investigator": "Pooja Bansal (Customer Support)",
            "ip_loc": "Online Merchant Portal",
            "suspect": "Hidden Auto-Debit Subscription",
            "desc": "Recurring monthly deduction of ₹320 without customer authorization.",
            "action": "Auto-debit mandate cancelled; Full ₹1,280 refunded."
        }
    },
    {
        "code": "CUST-80235",
        "name": "Arvind Joshi",
        "email": "arvind.joshi@indorefoods.in",
        "phone": "+91 98260 79460",
        "address": "45 Vijay Nagar Square",
        "city": "Indore",
        "state": "Madhya Pradesh",
        "risk_tier": "HIGH",
        "account_num": "ACT-4499-1122",
        "acc_type": "WEALTH_MANAGEMENT",
        "balance": 680000.00,
        "branch": "Indore Vijay Nagar Branch",
        "ticket": {
            "ticket_num": "FRD-2026-9097",
            "type": "Fake Share Market / Investment Scheme",
            "amount": 85000.00,
            "recovered": 0.00,
            "date": "2026-09-02 16:10:00",
            "channel": "Branch Visit",
            "severity": "CRITICAL",
            "status": "ESCALATED",
            "investigator": "Shreya Deshmukh (Support Lead)",
            "ip_loc": "Fake Stock Trading Group",
            "suspect": "Unregistered WhatsApp Trading Scheme",
            "desc": "Customer was lured by a fake stock trading group promising guaranteed 50% monthly returns.",
            "action": "Complaint forwarded to Cyber Crime Portal and local authorities."
        }
    },
    {
        "code": "CUST-80236",
        "name": "Divya Pillai",
        "email": "divya.pillai@coimbatoretextiles.in",
        "phone": "+91 98422 41607",
        "address": "480 RS Puram Main Road",
        "city": "Coimbatore",
        "state": "Tamil Nadu",
        "risk_tier": "MEDIUM",
        "account_num": "ACT-7711-2299",
        "acc_type": "BUSINESS",
        "balance": 142000.00,
        "branch": "Coimbatore RS Puram Branch",
        "ticket": {
            "ticket_num": "FRD-2026-9098",
            "type": "Multiple Small Unauthorized UPI Debits",
            "amount": 29400.00,
            "recovered": 29400.00,
            "date": "2026-09-01 13:45:00",
            "channel": "Online Banking Alert",
            "severity": "HIGH",
            "status": "RESOLVED",
            "investigator": "Rajesh Nair (Fraud Team)",
            "ip_loc": "UPI Gateway",
            "suspect": "Automated Micro-Debit Script",
            "desc": "10 consecutive unauthorized transactions under ₹3,000 executed within 5 minutes.",
            "action": "UPI ID blocked immediately; Full ₹29,400 credited back to account."
        }
    },
    {
        "code": "CUST-80237",
        "name": "Harish Bhatt",
        "email": "harish.bhatt@dehradunorganics.in",
        "phone": "+91 98970 61244",
        "address": "100 Rajpur Road",
        "city": "Dehradun",
        "state": "Uttarakhand",
        "risk_tier": "HIGH",
        "account_num": "ACT-1290-7733",
        "acc_type": "CHECKING",
        "balance": 275000.00,
        "branch": "Rajpur Road Branch",
        "ticket": {
            "ticket_num": "FRD-2026-9099",
            "type": "Fake Loan Application in Customer Name",
            "amount": 50000.00,
            "recovered": 50000.00,
            "date": "2026-08-30 10:15:00",
            "channel": "Online Banking Alert",
            "severity": "HIGH",
            "status": "RESOLVED",
            "investigator": "Vikram Joshi (Resolution Specialist)",
            "ip_loc": "Online Loan Portal",
            "suspect": "Fake KYC Document Submission",
            "desc": "Fraudster attempted to apply for a ₹50,000 instant personal loan using stolen PAN card copy.",
            "action": "Fraudulent loan application cancelled; CIBIL alert placed."
        }
    },
    {
        "code": "CUST-80238",
        "name": "Meera Nambiar",
        "email": "meera.nambiar@calicutshipping.in",
        "phone": "+91 94472 88321",
        "address": "88 Beach Road",
        "city": "Kozhikode",
        "state": "Kerala",
        "risk_tier": "MEDIUM",
        "account_num": "ACT-5544-7711",
        "acc_type": "CHECKING",
        "balance": 68000.00,
        "branch": "Beach Road Branch",
        "ticket": {
            "ticket_num": "FRD-2026-9100",
            "type": "Fake Public WiFi Login Scam",
            "amount": 16500.00,
            "recovered": 16500.00,
            "date": "2026-08-28 20:30:00",
            "channel": "Mobile Banking",
            "severity": "MEDIUM",
            "status": "RESOLVED",
            "investigator": "Pooja Bansal (Customer Support)",
            "ip_loc": "Public WiFi Hotspot",
            "suspect": "Fake WiFi Portal Page",
            "desc": "Customer connected to unverified public WiFi at airport which asked for bank login details.",
            "action": "Session terminated; Password reset required."
        }
    },
    {
        "code": "CUST-80239",
        "name": "Gaurav Kapoor",
        "email": "gaurav.kapoor@jaipurjewels.in",
        "phone": "+91 98290 71044",
        "address": "65 MI Road",
        "city": "Jaipur",
        "state": "Rajasthan",
        "risk_tier": "CRITICAL",
        "account_num": "ACT-9099-5522",
        "acc_type": "WEALTH_MANAGEMENT",
        "balance": 3800000.00,
        "branch": "Jaipur MI Road Branch",
        "ticket": {
            "ticket_num": "FRD-2026-9101",
            "type": "Account Lockout & Extortion Attempt",
            "amount": 500000.00,
            "recovered": 500000.00,
            "date": "2026-08-27 15:40:00",
            "channel": "Customer Helpline",
            "severity": "CRITICAL",
            "status": "UNDER_INVESTIGATION",
            "investigator": "Shreya Deshmukh (Support Lead)",
            "ip_loc": "Anonymous Email Server",
            "suspect": "Extortion Email",
            "desc": "Customer received extortion email claiming their computer was hacked and demanding money.",
            "action": "Customer advised not to pay; Bank account secured; Zero money lost."
        }
    },
    {
        "code": "CUST-80240",
        "name": "Karthik Subramanian",
        "email": "karthik.s@fintechnova.in",
        "phone": "+91 99887 76655",
        "address": "Indiranagar 100ft Road",
        "city": "Bengaluru",
        "state": "Karnataka",
        "risk_tier": "HIGH",
        "account_num": "ACT-6677-8899",
        "acc_type": "CHECKING",
        "balance": 92000.00,
        "branch": "Bengaluru Whitefield Branch",
        "ticket": {
            "ticket_num": "FRD-2026-9102",
            "type": "Fake QR Code Scam",
            "amount": 8900.00,
            "recovered": 8900.00,
            "date": "2026-08-26 12:10:00",
            "channel": "Mobile Banking",
            "severity": "HIGH",
            "status": "RESOLVED",
            "investigator": "Pooja Bansal (Customer Support)",
            "ip_loc": "UPI VPA merchant.fraud@okhdfcbank",
            "suspect": "Overlaid QR Sticker on Merchant Counter",
            "desc": "Customer scanned a QR code sticker pasted over merchant's genuine standee.",
            "action": "UPI ID frozen via NPCI portal; ₹8,900 credited back."
        }
    },
    {
        "code": "CUST-80241",
        "name": "Kavita Krishnan",
        "email": "kavita.krishnan@maduraimedical.in",
        "phone": "+91 98430 49608",
        "address": "18 West Veli Street",
        "city": "Madurai",
        "state": "Tamil Nadu",
        "risk_tier": "MEDIUM",
        "account_num": "ACT-4422-9900",
        "acc_type": "SAVINGS",
        "balance": 135000.00,
        "branch": "Madurai West Branch",
        "ticket": {
            "ticket_num": "FRD-2026-9103",
            "type": "Unauthorized Auto-Debit Setup",
            "amount": 3400.00,
            "recovered": 3400.00,
            "date": "2026-08-25 18:00:00",
            "channel": "Website Help Form",
            "severity": "MEDIUM",
            "status": "RESOLVED",
            "investigator": "Rajesh Nair (Fraud Team)",
            "ip_loc": "Mandate Registration Portal",
            "suspect": "Bogus Gym Membership Mandate",
            "desc": "Unauthorized auto-debit mandate registered using account details found on discarded bank slip.",
            "action": "Mandate cancelled immediately; ₹3,400 refunded."
        }
    },
    {
        "code": "CUST-80242",
        "name": "Sanjay Chawla",
        "email": "sanjay.chawla@lucknowhandicrafts.in",
        "phone": "+91 98390 98765",
        "address": "100 Hazratganj Main Market",
        "city": "Lucknow",
        "state": "Uttar Pradesh",
        "risk_tier": "HIGH",
        "account_num": "ACT-1144-8833",
        "acc_type": "BUSINESS",
        "balance": 310000.00,
        "branch": "Hazratganj Branch",
        "ticket": {
            "ticket_num": "FRD-2026-9104",
            "type": "Cloned Phone Banking Access",
            "amount": 42000.00,
            "recovered": 25000.00,
            "date": "2026-08-24 22:15:00",
            "channel": "Mobile Banking",
            "severity": "HIGH",
            "status": "UNDER_INVESTIGATION",
            "investigator": "Vikram Joshi (Resolution Specialist)",
            "ip_loc": "Cloned Mobile Device",
            "suspect": "Cloned Device Profile",
            "desc": "Unauthorized transfer initiated from a cloned mobile phone device ID.",
            "action": "Device registration invalidated; Password reset enforced."
        }
    },
    {
        "code": "CUST-80243",
        "name": "Ritu Sen",
        "email": "ritu.sen@kolkatatech.in",
        "phone": "+91 98300 20189",
        "address": "77 Park Street",
        "city": "Kolkata",
        "state": "West Bengal",
        "risk_tier": "CRITICAL",
        "account_num": "ACT-7733-6622",
        "acc_type": "BUSINESS",
        "balance": 1250000.00,
        "branch": "Kolkata Park Street Branch",
        "ticket": {
            "ticket_num": "FRD-2026-9105",
            "type": "Unauthorized Online Wire Attempt",
            "amount": 195000.00,
            "recovered": 195000.00,
            "date": "2026-08-23 14:10:00",
            "channel": "Online Banking Alert",
            "severity": "CRITICAL",
            "status": "RESOLVED",
            "investigator": "Shreya Deshmukh (Support Lead)",
            "ip_loc": "Suspicious Browser Extension",
            "suspect": "Malicious Web Extension",
            "desc": "Customer's computer browser was infected with a rogue extension attempting to modify transfer beneficiary.",
            "action": "Safety system stopped transaction packet; ₹1,95,000 completely saved."
        }
    }
]

def run_db_setup():
    print(f"[*] Connecting to PostgreSQL at {DB_HOST}:{DB_PORT} as '{DB_USER}'...")
    
    # 1. Connect to default postgres DB to check/create target DB
    try:
        conn = pg8000.dbapi.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            database="postgres"
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (TARGET_DB,))
        exists = cursor.fetchone()
        
        if not exists:
            print(f"[*] Creating database '{TARGET_DB}'...")
            cursor.execute(f"CREATE DATABASE {TARGET_DB} WITH ENCODING 'UTF8';")
            print(f"[+] Database '{TARGET_DB}' created successfully!")
        else:
            print(f"[+] Database '{TARGET_DB}' already exists.")
            
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[-] Error connecting to PostgreSQL default database: {e}")
        sys.exit(1)

    # 2. Connect to target database and create tables
    print(f"[*] Connecting to '{TARGET_DB}' database...")
    try:
        conn = pg8000.dbapi.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            database=TARGET_DB
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Read and execute schema.sql
        print("[*] Applying schema tables and indexes...")
        with open("schema.sql", "r", encoding="utf-8") as f:
            schema_sql = f.read()
        
        try:
            cursor._c.execute_simple(schema_sql)
        except Exception as ex:
            print(f"[!] Simple query execution notice: {ex}")
        print("[+] Schema applied successfully!")

        # Seed Staff Users and Employees (Pooja Deshmukh & SOC Team)
        import hashlib
        p_hash = hashlib.sha256("Password@123".encode("utf-8")).hexdigest()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS staff_users (
                user_id SERIAL PRIMARY KEY,
                username VARCHAR(80) UNIQUE NOT NULL,
                password_hash VARCHAR(128) NOT NULL,
                password_plain VARCHAR(80) DEFAULT 'Password@123',
                full_name VARCHAR(100) NOT NULL,
                role VARCHAR(40) DEFAULT 'INVESTIGATOR',
                email VARCHAR(120) NOT NULL,
                department VARCHAR(100),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                employee_id SERIAL PRIMARY KEY,
                employee_code VARCHAR(20) UNIQUE,
                username VARCHAR(80) UNIQUE NOT NULL,
                password_hash VARCHAR(128) NOT NULL,
                password_plain VARCHAR(80) DEFAULT 'Password@123',
                full_name VARCHAR(100) NOT NULL,
                role VARCHAR(40) DEFAULT 'INVESTIGATOR',
                email VARCHAR(120) NOT NULL,
                phone VARCHAR(25),
                department VARCHAR(100),
                designation VARCHAR(100),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        cursor.execute("""
            INSERT INTO staff_users (username, password_hash, password_plain, full_name, role, email, department, is_active)
            VALUES 
                ('pooja.deshmukh', %s, 'Password@123', 'Pooja Deshmukh', 'SOC_ANALYST', 'pooja.deshmukh@automationedge.ai', 'SOC Operations', TRUE),
                ('investigator1', %s, 'Password@123', 'SOC Operations Team', 'FRAUD_INVESTIGATOR', 'soc.fraud@bank.internal', 'Cyber Defense', TRUE),
                ('manager', %s, 'Password@123', 'Vikram Malhotra', 'MANAGER', 'vikram.m@bank.internal', 'Fraud Risk Management (All Access)', TRUE)
            ON CONFLICT (username) DO NOTHING;
        """, (p_hash, p_hash, p_hash))

        cursor.execute("""
            INSERT INTO employees (employee_code, username, password_hash, password_plain, full_name, role, email, phone, department, designation, is_active)
            VALUES 
                ('EMP-0101', 'pooja.deshmukh', %s, 'Password@123', 'Pooja Deshmukh', 'SOC_ANALYST', 'pooja.deshmukh@automationedge.ai', '+91 98201 00101', 'SOC Operations', 'Senior SOC Analyst', TRUE),
                ('EMP-0001', 'investigator1', %s, 'Password@123', 'SOC Operations Team', 'FRAUD_INVESTIGATOR', 'soc.fraud@bank.internal', '+91 98201 00001', 'Cyber Defense', 'Fraud Lead', TRUE),
                ('EMP-0002', 'manager', %s, 'Password@123', 'Vikram Malhotra', 'MANAGER', 'vikram.m@bank.internal', '+91 98201 00002', 'Fraud Risk Management (All Access)', 'Branch Manager', TRUE)
            ON CONFLICT (username) DO NOTHING;
        """, (p_hash, p_hash, p_hash))

        # 3. Seed Customers, Accounts, Fraud Tickets, Transactions, and Audit Logs
        print(f"[*] Seeding {len(CUSTOMERS_DATA)} Indian customer fraud records...")
        
        for item in CUSTOMERS_DATA:
            t = item["ticket"]
            cust_name = item["name"]
            
            # Insert Customer
            cursor.execute("""
                INSERT INTO customers (customer_code, customer_name, full_name, email, phone, address, city, state, country, risk_tier)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING customer_id;
            """, (
                item["code"], cust_name, cust_name, item["email"], item["phone"],
                item["address"], item["city"], item["state"], "India", item["risk_tier"]
            ))
            cust_id = cursor.fetchone()[0]
            
            # Insert Account
            cursor.execute("""
                INSERT INTO customer_accounts (customer_id, customer_name, account_number, account_type, balance, currency, branch, opened_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING account_id;
            """, (
                cust_id, cust_name, item["account_num"], item["acc_type"], item["balance"],
                "INR", item["branch"], "2023-01-15"
            ))
            
            # Insert Fraud Ticket
            cursor.execute("""
                INSERT INTO fraud_tickets (
                    ticket_number, customer_id, customer_name, account_number, incident_type,
                    amount_involved, recovered_amount, incident_date, reported_channel,
                    severity, status, assigned_investigator, flagged_ip_or_location,
                    suspect_entity, description, action_taken
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING ticket_id;
            """, (
                t["ticket_num"], cust_id, cust_name, item["account_num"], t["type"],
                t["amount"], t["recovered"], t["date"], t["channel"],
                t["severity"], t["status"], t["investigator"], t["ip_loc"],
                t["suspect"], t["desc"], t["action"]
            ))
            
            # Insert Linked Suspicious Transaction
            cursor.execute("""
                INSERT INTO transactions (
                    txn_reference, customer_id, customer_name, account_number, amount,
                    txn_type, merchant_or_recipient, channel, ip_address,
                    is_fraud_flagged, fraud_risk_score, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """, (
                f"TXN-{t['ticket_num'][-4:]}-01", cust_id, cust_name, item["account_num"], t["amount"],
                "ONLINE_TRANSFER", t["suspect"], t["channel"], t["ip_loc"][:40],
                True, 95 if t["severity"] == "CRITICAL" else (80 if t["severity"] == "HIGH" else 60),
                "BLOCKED" if t["status"] in ["FROZEN", "RESOLVED"] else "HELD"
            ))
            
            # Insert Audit Log
            cursor.execute("""
                INSERT INTO audit_logs (ticket_number, customer_name, actor, action, details, ip_address)
                VALUES (%s, %s, %s, %s, %s, %s);
            """, (
                t["ticket_num"], cust_name, t["investigator"], f"STATUS_UPDATE_{t['status']}",
                f"Fraud complaint triage: {t['desc'][:100]}...", "Branch Office Terminal"
            ))

        # Check total counts
        cursor.execute("SELECT COUNT(*) FROM customers;")
        cust_cnt = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM fraud_tickets;")
        ticket_cnt = cursor.fetchone()[0]
        
        print(f"\n[SUCCESS] PostgreSQL Database '{TARGET_DB}' fully initialized with Indian customer records!")
        print(f" -> Total Indian Customers created: {cust_cnt}")
        print(f" -> Total Fraud Complaints created: {ticket_cnt}")
        print(f" -> Ready for pgAdmin 4 inspection under PostgreSQL (user: postgres, db: {TARGET_DB})\n")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[-] Error seeding database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_db_setup()
