"""
Customer_GraphAPI - LangGraph Forensic Multi-Agent Engine
Stateful Agent Workflow for Graph RAG Fraud Investigation & Syndicate Discovery.
"""

import time
import json
import logging
from typing import Dict, List, Any, Optional, TypedDict, Literal
from datetime import datetime

from graph_engine import knowledge_graph_engine, FraudKnowledgeGraph
import pg8000.dbapi
from config import DB_HOST, DB_PORT, DB_USER, DB_PASS, DB_NAME, OPENAI_API_KEY, OPENAI_MODEL

logger = logging.getLogger("LangGraphAgent")

# -------------------------------------------------------------
# 1. LangGraph State Schema Definition
# -------------------------------------------------------------
class FraudInvestigationState(TypedDict):
    """
    Central State passed through all nodes in the LangGraph execution pipeline.
    """
    ticket_query: str                          # Input: Ticket ID or Ticket Number
    ticket_data: Dict[str, Any]                # Forensic ticket record from DB
    customer_profile: Dict[str, Any]           # Customer KYC & accounts
    subgraph: Dict[str, Any]                   # 2-hop Graph RAG neighborhood
    is_syndicate: bool                         # True if connected to other victims
    syndicate_details: Dict[str, Any]          # Summary of the fraud ring
    risk_score: int                            # Calculated Threat Score (0 - 100)
    risk_level: str                            # CRITICAL, HIGH, MEDIUM, LOW
    mitigation_actions: List[Dict[str, str]]   # Recommended emergency actions
    step_traces: List[Dict[str, Any]]          # Node-by-node execution logs for UI
    forensic_report: str                       # Final synthesized intelligence dossier
    status: str                                # COMPLETED / FAILED / ESCALATED


# -------------------------------------------------------------
# 2. StateGraph Nodes (Agent Functions)
# -------------------------------------------------------------

def node_fetch_ticket(state: FraudInvestigationState) -> Dict[str, Any]:
    """
    Node 1: Data Acquisition Agent
    Fetches the ticket record and customer profile from PostgreSQL.
    """
    t_query = state.get("ticket_query", "").strip()
    traces = list(state.get("step_traces", []))
    t0 = time.time()

    conn = pg8000.dbapi.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, database=DB_NAME
    )
    conn.autocommit = True
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT 
                t.ticket_id, t.ticket_number, t.customer_id, c.full_name, c.email, c.phone, c.risk_tier,
                t.account_number, ca.account_type, ca.balance, ca.status as account_status,
                t.incident_type, t.amount_involved, t.severity, t.status, t.assigned_investigator,
                t.suspect_entity, t.flagged_ip_or_location, t.description, t.action_taken
            FROM fraud_tickets t
            JOIN customers c ON t.customer_id = c.customer_id
            LEFT JOIN customer_accounts ca ON (t.customer_id = ca.customer_id AND t.account_number = ca.account_number)
            WHERE t.ticket_id = %s OR t.ticket_number = %s
            LIMIT 1;
        """, (int(t_query) if t_query.isdigit() else -1, t_query))
        
        row = cursor.fetchone()
        if not row:
            # Fallback to recent ticket if query not found
            cursor.execute("""
                SELECT 
                    t.ticket_id, t.ticket_number, t.customer_id, c.full_name, c.email, c.phone, c.risk_tier,
                    t.account_number, ca.account_type, ca.balance, ca.status as account_status,
                    t.incident_type, t.amount_involved, t.severity, t.status, t.assigned_investigator,
                    t.suspect_entity, t.flagged_ip_or_location, t.description, t.action_taken
                FROM fraud_tickets t
                JOIN customers c ON t.customer_id = c.customer_id
                LEFT JOIN customer_accounts ca ON (t.customer_id = ca.customer_id AND t.account_number = ca.account_number)
                ORDER BY t.ticket_id DESC LIMIT 1;
            """)
            row = cursor.fetchone()

        if not row:
            raise ValueError(f"No fraud tickets found in database matching '{t_query}'.")

        ticket_data = {
            "ticket_id": row[0],
            "ticket_number": row[1],
            "customer_id": row[2],
            "customer_name": row[3],
            "email": row[4],
            "phone": row[5],
            "risk_tier": row[6],
            "account_number": row[7],
            "account_type": row[8] or "SAVINGS",
            "account_balance": float(row[9]) if row[9] is not None else 0.0,
            "account_status": row[10] or "ACTIVE",
            "incident_type": row[11],
            "amount_involved": float(row[12]),
            "severity": row[13],
            "ticket_status": row[14],
            "assigned_investigator": row[15],
            "suspect_entity": row[16] or "Unverified Beneficiary",
            "flagged_ip": row[17] or "127.0.0.1",
            "description": row[18],
            "action_taken": row[19]
        }

        traces.append({
            "node": "node_fetch_ticket",
            "agent": "Data Ingestion Agent",
            "time_ms": round((time.time() - t0) * 1000, 2),
            "status": "SUCCESS",
            "detail": f"Loaded ticket {ticket_data['ticket_number']} for {ticket_data['customer_name']} (₹{ticket_data['amount_involved']:,.2f} - {ticket_data['incident_type']})"
        })

        return {
            "ticket_data": ticket_data,
            "customer_profile": {
                "customer_id": ticket_data["customer_id"],
                "name": ticket_data["customer_name"],
                "risk_tier": ticket_data["risk_tier"],
                "account_number": ticket_data["account_number"]
            },
            "step_traces": traces
        }
    finally:
        cursor.close()
        conn.close()


def node_extract_graph_subgraph(state: FraudInvestigationState) -> Dict[str, Any]:
    """
    Node 2: Graph RAG Neighborhood Extractor Agent
    Traverses the NetworkX knowledge graph to extract 2-hop connected entities (suspects, accounts, IPs).
    """
    t0 = time.time()
    traces = list(state.get("step_traces", []))
    ticket_data = state.get("ticket_data", {})
    t_id = str(ticket_data.get("ticket_id", ""))

    subgraph = knowledge_graph_engine.get_neighborhood_subgraph(f"TICK_{t_id}", hops=2)

    traces.append({
        "node": "node_extract_graph_subgraph",
        "agent": "Graph RAG Topology Agent",
        "time_ms": round((time.time() - t0) * 1000, 2),
        "status": "SUCCESS",
        "detail": f"Extracted 2-hop knowledge graph: {subgraph['total_nodes']} connected nodes and {subgraph['total_edges']} edges."
    })

    return {
        "subgraph": subgraph,
        "step_traces": traces
    }


def node_detect_syndicate(state: FraudInvestigationState) -> Dict[str, Any]:
    """
    Node 3: Fraud Ring & Mule Account Detector Agent
    Analyzes whether the suspect entity or IP is linked to multiple victims across the entire bank graph.
    """
    t0 = time.time()
    traces = list(state.get("step_traces", []))
    ticket_data = state.get("ticket_data", {})
    suspect_entity = ticket_data.get("suspect_entity", "").strip()

    all_syndicates = knowledge_graph_engine.detect_fraud_syndicates()
    
    # Check if the suspect entity in this ticket matches an identified syndicate hub
    matched_syndicate = None
    for syn in all_syndicates:
        if syn["suspect_entity"].lower() == suspect_entity.lower():
            matched_syndicate = syn
            break

    is_syndicate = matched_syndicate is not None
    details = matched_syndicate if matched_syndicate else {
        "suspect_entity": suspect_entity,
        "victim_count": 1,
        "victims": [ticket_data.get("customer_name", "Primary Victim")],
        "total_exposure_inr": ticket_data.get("amount_involved", 0.0),
        "risk_level": "ISOLATED"
    }

    traces.append({
        "node": "node_detect_syndicate",
        "agent": "Syndicate Discovery Agent",
        "time_ms": round((time.time() - t0) * 1000, 2),
        "status": "ALERT" if is_syndicate else "SUCCESS",
        "detail": (
            f"🚨 SYNDICATE DETECTED: Suspect '{suspect_entity}' is linked to {details['victim_count']} victims with ₹{details['total_exposure_inr']:,.2f} total risk exposure!"
            if is_syndicate else
            f"Isolated incident pattern: No secondary victim links found for '{suspect_entity}'."
        )
    })

    return {
        "is_syndicate": is_syndicate,
        "syndicate_details": details,
        "step_traces": traces
    }


def node_assess_risk_and_reason(state: FraudInvestigationState) -> Dict[str, Any]:
    """
    Node 4: Cyber Forensic Reasoning & Risk Scoring Agent
    Combines Graph Topology, Financial Impact, and Incident Classification into a normalized 0-100 Threat Score.
    """
    t0 = time.time()
    traces = list(state.get("step_traces", []))
    ticket_data = state.get("ticket_data", {})
    is_syndicate = state.get("is_syndicate", False)
    syn_details = state.get("syndicate_details", {})

    amount = float(ticket_data.get("amount_involved", 0.0))
    severity = str(ticket_data.get("severity", "MEDIUM")).upper()

    # Multi-factor score calculation
    score = 30  # Baseline
    
    # Financial Impact weight
    if amount >= 100000.0:
        score += 30
    elif amount >= 50000.0:
        score += 20
    elif amount >= 20000.0:
        score += 10

    # Severity tier
    if severity == "CRITICAL":
        score += 20
    elif severity == "HIGH":
        score += 15

    # Syndicate multiplier
    if is_syndicate:
        score += 25
        if syn_details.get("victim_count", 1) >= 3:
            score += 10

    score = min(100, max(10, score))
    risk_level = "CRITICAL" if score >= 80 else ("HIGH" if score >= 60 else ("MEDIUM" if score >= 40 else "LOW"))

    traces.append({
        "node": "node_assess_risk_and_reason",
        "agent": "Forensic Reasoning Agent",
        "time_ms": round((time.time() - t0) * 1000, 2),
        "status": "SUCCESS",
        "detail": f"Calculated Composite Threat Score: {score}/100 [{risk_level}]. Factors: ₹{amount:,.2f} volume + {severity} severity + {'Syndicate Network Hub' if is_syndicate else 'Single Endpoint'}."
    })

    return {
        "risk_score": score,
        "risk_level": risk_level,
        "step_traces": traces
    }


def node_critical_escalate(state: FraudInvestigationState) -> Dict[str, Any]:
    """
    Node 5A: Emergency Escalation Node (Conditional Path for High Risk / Syndicate)
    Triggers emergency asset lock recommendations and NPCI cyber fraud escalation.
    """
    t0 = time.time()
    traces = list(state.get("step_traces", []))
    ticket_data = state.get("ticket_data", {})
    acc_num = ticket_data.get("account_number", "")
    suspect = ticket_data.get("suspect_entity", "")

    actions = [
        {"action": "EMERGENCY_FREEZE_ACCOUNT", "target": acc_num, "priority": "P0_IMMEDIATE", "reason": "Prevent secondary unauthorized withdrawals."},
        {"action": "BLACKLIST_BENEFICIARY_UPI", "target": suspect, "priority": "P0_IMMEDIATE", "reason": "Flagged as high-velocity fraud syndicate hub."},
        {"action": "REPORT_NPCI_CFCFR_PORTAL", "target": f"TICKET-{ticket_data.get('ticket_number')}", "priority": "P1_URGENT", "reason": "Lodge inter-bank cyber crime alert on Citizen Financial Cyber Fraud Reporting System."},
        {"action": "DISPATCH_SECURITY_ALERT_SMS", "target": ticket_data.get("phone", ""), "priority": "P1_URGENT", "reason": "Notify customer and invalidate active mobile banking tokens."}
    ]

    traces.append({
        "node": "node_critical_escalate",
        "agent": "Emergency Response Agent",
        "time_ms": round((time.time() - t0) * 1000, 2),
        "status": "ALERT",
        "detail": f"Generated 4 Critical Emergency Mitigation Protocols (Account Freeze, UPI Blacklist, NPCI Escalation)."
    })

    return {
        "mitigation_actions": actions,
        "step_traces": traces
    }


def node_standard_mitigate(state: FraudInvestigationState) -> Dict[str, Any]:
    """
    Node 5B: Standard Mitigation Node (Conditional Path for Low/Medium Risk)
    Generates standard investigation & dispute procedures.
    """
    t0 = time.time()
    traces = list(state.get("step_traces", []))
    ticket_data = state.get("ticket_data", {})
    acc_num = ticket_data.get("account_number", "")

    actions = [
        {"action": "TEMPORARY_LIMIT_RESTRICTION", "target": acc_num, "priority": "P2_MEDIUM", "reason": "Reduce daily online transfer limit pending verification."},
        {"action": "REQUEST_CUSTOMER_TRANSACTION_DISPUTE", "target": ticket_data.get("customer_name", ""), "priority": "P2_MEDIUM", "reason": "Obtain signed chargeback and dispute declaration."},
        {"action": "ASSIGN_FRAUD_ANALYST_QUEUE", "target": ticket_data.get("assigned_investigator", "SOC Team"), "priority": "P3_STANDARD", "reason": "Standard operational triage."}
    ]

    traces.append({
        "node": "node_standard_mitigate",
        "agent": "Standard Resolution Agent",
        "time_ms": round((time.time() - t0) * 1000, 2),
        "status": "SUCCESS",
        "detail": "Generated standard customer dispute and verification protocols."
    })

    return {
        "mitigation_actions": actions,
        "step_traces": traces
    }


def node_finalize_report(state: FraudInvestigationState) -> Dict[str, Any]:
    """
    Node 6: Final Synthesis Agent
    Compiles full Graph RAG intelligence, reasoning traces, and action plans into a Markdown Forensic Dossier.
    """
    t0 = time.time()
    traces = list(state.get("step_traces", []))
    ticket = state.get("ticket_data", {})
    syn = state.get("syndicate_details", {})
    is_syn = state.get("is_syndicate", False)
    actions = state.get("mitigation_actions", [])
    score = state.get("risk_score", 50)
    level = state.get("risk_level", "MEDIUM")

    # Generate Markdown Forensic Report
    report = f"""# 🛡️ CYBER FORENSIC DOSSIER & GRAPHRAG INTELLIGENCE REPORT
**Report Reference:** `FORENSIC-{ticket.get('ticket_number')}`  
**Generated At:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}`  
**Risk Threat Rating:** **{score}/100 [{level}]**  

---

### 1. Incident Overview
- **Ticket ID:** `{ticket.get('ticket_number')}` (Internal ID: `{ticket.get('ticket_id')}`)
- **Victim Customer:** `{ticket.get('customer_name')}` (Risk Tier: `{ticket.get('risk_tier')}`)
- **Compromised Account:** `{ticket.get('account_number')}` ({ticket.get('account_type')} - Current Balance: ₹{ticket.get('account_balance', 0):,.2f})
- **Incident Categorization:** `{ticket.get('incident_type')}`
- **Disputed Financial Amount:** **₹{ticket.get('amount_involved', 0):,.2f}**
- **Flagged Suspect Entity:** `{ticket.get('suspect_entity')}`
- **Originating IP / Location:** `{ticket.get('flagged_ip')}`

---

### 2. Graph RAG Knowledge Topology & Fraud Ring Analysis
- **Syndicate Status:** {'🚨 **CONFIRMED MULTI-VICTIM FRAUD RING**' if is_syn else '🟢 Isolated Single-Target Incident'}
- **Connected Victims in Bank Graph:** **{syn.get('victim_count', 1)} Victims**
- **Coordinated Total Exposure:** **₹{syn.get('total_exposure_inr', ticket.get('amount_involved', 0)):,.2f}**
- **Graph Topology:** Connected to {state.get('subgraph', {}).get('total_nodes', 0)} multi-hop nodes and {state.get('subgraph', {}).get('total_edges', 0)} directed transaction edges.

---

### 3. Recommended Automated Mitigation Protocols
"""
    for idx, act in enumerate(actions, 1):
        report += f"{idx}. **[{act['priority']}] `{act['action']}`** on `{act['target']}`\n   - *Rationale:* {act['reason']}\n"

    report += f"""
---
*Investigation executed autonomously by LangGraph Multi-Agent Engine with NetworkX Graph RAG.*
"""

    traces.append({
        "node": "node_finalize_report",
        "agent": "Dossier Synthesis Agent",
        "time_ms": round((time.time() - t0) * 1000, 2),
        "status": "SUCCESS",
        "detail": "Forensic Dossier compiled and finalized for SOC Operations."
    })

    return {
        "forensic_report": report,
        "status": "COMPLETED",
        "step_traces": traces
    }


# -------------------------------------------------------------
# 3. LangGraph Execution Engine & State Machine
# -------------------------------------------------------------

class LangGraphFraudWorkflow:
    """
    Executes the directed state graph with deterministic transitions and conditional branching.
    """
    def __init__(self):
        self.workflow_history = []

    def execute(self, ticket_query: str) -> FraudInvestigationState:
        """
        Runs the full LangGraph pipeline from start to finish.
        """
        # Initial State
        state: FraudInvestigationState = {
            "ticket_query": ticket_query,
            "ticket_data": {},
            "customer_profile": {},
            "subgraph": {},
            "is_syndicate": False,
            "syndicate_details": {},
            "risk_score": 0,
            "risk_level": "UNKNOWN",
            "mitigation_actions": [],
            "step_traces": [],
            "forensic_report": "",
            "status": "RUNNING"
        }

        # Step 1: Ingestion
        res1 = node_fetch_ticket(state)
        state.update(res1)

        # Step 2: Graph RAG Subgraph Extraction
        res2 = node_extract_graph_subgraph(state)
        state.update(res2)

        # Step 3: Syndicate Discovery
        res3 = node_detect_syndicate(state)
        state.update(res3)

        # Step 4: Multi-factor Risk Reasoning
        res4 = node_assess_risk_and_reason(state)
        state.update(res4)

        # Conditional Branching Edge:
        # If Risk >= 70 or Syndicate detected -> Critical Escalation Path
        # Else -> Standard Mitigation Path
        if state["risk_score"] >= 70 or state["is_syndicate"]:
            res5 = node_critical_escalate(state)
        else:
            res5 = node_standard_mitigate(state)
        state.update(res5)

        # Step 6: Final Dossier Synthesis
        res6 = node_finalize_report(state)
        state.update(res6)

        # Save to memory history
        self.workflow_history.insert(0, {
            "run_id": f"RUN-{len(self.workflow_history) + 1:04d}",
            "ticket_number": state["ticket_data"].get("ticket_number"),
            "customer_name": state["ticket_data"].get("customer_name"),
            "risk_score": state["risk_score"],
            "risk_level": state["risk_level"],
            "is_syndicate": state["is_syndicate"],
            "total_nodes": state["subgraph"].get("total_nodes", 0),
            "timestamp": datetime.now().isoformat(),
            "traces": state["step_traces"]
        })

        return state

# Singleton Agent Engine
langgraph_fraud_agent = LangGraphFraudWorkflow()
