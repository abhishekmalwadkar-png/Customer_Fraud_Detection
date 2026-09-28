"""
Customer_GraphAPI - Knowledge Graph Engine
Powered by NetworkX and PostgreSQL (bank_fraud_portal).
Builds entity relationship graphs, extracts subgraphs, and detects multi-victim fraud syndicates.
"""

import time
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
import networkx as nx
import pg8000.dbapi

from config import DB_HOST, DB_PORT, DB_USER, DB_PASS, DB_NAME

logger = logging.getLogger("GraphEngine")

# Color and Styling System for Vis.js Graph Visualization
NODE_STYLES = {
    "CUSTOMER": {
        "color": {"background": "#0284c7", "border": "#38bdf8", "highlight": {"background": "#0369a1", "border": "#7dd3fc"}},
        "size": 26,
        "shape": "dot",
        "font": {"color": "#f8fafc", "size": 13, "face": "Inter, sans-serif"}
    },
    "ACCOUNT": {
        "color": {"background": "#0d9488", "border": "#2dd4bf", "highlight": {"background": "#0f766e", "border": "#5eead4"}},
        "size": 22,
        "shape": "dot",
        "font": {"color": "#f8fafc", "size": 12, "face": "Inter, sans-serif"}
    },
    "TICKET_CRITICAL": {
        "color": {"background": "#dc2626", "border": "#f87171", "highlight": {"background": "#b91c1c", "border": "#fca5a5"}},
        "size": 24,
        "shape": "hexagon",
        "font": {"color": "#f8fafc", "size": 12, "face": "Inter, sans-serif"}
    },
    "TICKET_HIGH": {
        "color": {"background": "#ea580c", "border": "#fb923c", "highlight": {"background": "#c2410c", "border": "#fdba74"}},
        "size": 22,
        "shape": "hexagon",
        "font": {"color": "#f8fafc", "size": 12, "face": "Inter, sans-serif"}
    },
    "TICKET_NORMAL": {
        "color": {"background": "#d97706", "border": "#fbbf24", "highlight": {"background": "#b45309", "border": "#fde68a"}},
        "size": 20,
        "shape": "hexagon",
        "font": {"color": "#f8fafc", "size": 12, "face": "Inter, sans-serif"}
    },
    "SUSPECT": {
        "color": {"background": "#991b1b", "border": "#ef4444", "highlight": {"background": "#7f1d1d", "border": "#f87171"}},
        "size": 32,
        "shape": "diamond",
        "font": {"color": "#fef2f2", "size": 14, "face": "Inter, sans-serif", "bold": "true"}
    },
    "IP_LOCATION": {
        "color": {"background": "#7c3aed", "border": "#a78bfa", "highlight": {"background": "#6d28d9", "border": "#c4b5fd"}},
        "size": 18,
        "shape": "triangle",
        "font": {"color": "#f8fafc", "size": 11, "face": "Inter, sans-serif"}
    },
    "INVESTIGATOR": {
        "color": {"background": "#059669", "border": "#34d399", "highlight": {"background": "#047857", "border": "#6ee7b7"}},
        "size": 20,
        "shape": "square",
        "font": {"color": "#f8fafc", "size": 11, "face": "Inter, sans-serif"}
    }
}

class FraudKnowledgeGraph:
    """Enterprise Knowledge Graph Manager for Banking Fraud Networks."""

    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self.last_built_at = 0.0

    def get_db_connection(self):
        """Establish direct connection to PostgreSQL."""
        return pg8000.dbapi.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME
        )

    def refresh_from_postgres(self) -> nx.MultiDiGraph:
        """Query PostgreSQL and reconstruct the in-memory NetworkX MultiDiGraph."""
        g = nx.MultiDiGraph()
        conn = self.get_db_connection()
        conn.autocommit = True
        cursor = conn.cursor()

        try:
            # 1. Fetch Customers
            cursor.execute("""
                SELECT customer_id, customer_code, full_name, email, phone, city, state, risk_tier
                FROM customers;
            """)
            for c in cursor.fetchall():
                c_id, code, name, email, phone, city, state, risk = c
                node_id = f"CUST_{c_id}"
                g.add_node(
                    node_id,
                    node_type="CUSTOMER",
                    label=name,
                    title=f"<b>Customer:</b> {name}<br><b>Code:</b> {code}<br><b>Risk:</b> {risk}<br><b>Phone:</b> {phone}<br><b>City:</b> {city or 'Unknown'}",
                    details={
                        "customer_id": c_id,
                        "code": code,
                        "name": name,
                        "email": email,
                        "phone": phone,
                        "city": city,
                        "state": state,
                        "risk_tier": risk
                    }
                )

            # 2. Fetch Customer Accounts
            cursor.execute("""
                SELECT account_id, customer_id, account_number, account_type, balance, branch, status
                FROM customer_accounts;
            """)
            for a in cursor.fetchall():
                acc_id, cust_id, acc_num, acc_type, bal, branch, status = a
                acc_node = f"ACC_{acc_num}"
                cust_node = f"CUST_{cust_id}"
                
                g.add_node(
                    acc_node,
                    node_type="ACCOUNT",
                    label=acc_num,
                    title=f"<b>Account:</b> {acc_num}<br><b>Type:</b> {acc_type}<br><b>Balance:</b> ₹{float(bal):,.2f}<br><b>Status:</b> {status}<br><b>Branch:</b> {branch}",
                    details={
                        "account_id": acc_id,
                        "account_number": acc_num,
                        "account_type": acc_type,
                        "balance": float(bal),
                        "branch": branch,
                        "status": status
                    }
                )

                if cust_node in g:
                    g.add_edge(cust_node, acc_node, key="OWNS_ACCOUNT", relationship="OWNS_ACCOUNT", label="owns")

            # 3. Fetch Fraud Tickets & Relationships
            cursor.execute("""
                SELECT 
                    ticket_id, ticket_number, customer_id, account_number, incident_type,
                    amount_involved, recovered_amount, incident_date, severity, status,
                    assigned_investigator, suspect_entity, flagged_ip_or_location, description
                FROM fraud_tickets;
            """)
            for t in cursor.fetchall():
                t_id, t_num, c_id, acc_num, inc_type, amount, rec_amt, inc_date, sev, st, inv, suspect, ip_loc, desc = t
                t_node = f"TICK_{t_id}"
                cust_node = f"CUST_{c_id}"
                acc_node = f"ACC_{acc_num}"

                t_type = "TICKET_CRITICAL" if sev == "CRITICAL" else ("TICKET_HIGH" if sev == "HIGH" else "TICKET_NORMAL")
                g.add_node(
                    t_node,
                    node_type=t_type,
                    label=t_num,
                    title=f"<b>Ticket:</b> {t_num}<br><b>Incident:</b> {inc_type}<br><b>Amount:</b> ₹{float(amount):,.2f}<br><b>Severity:</b> {sev}<br><b>Status:</b> {st}",
                    details={
                        "ticket_id": t_id,
                        "ticket_number": t_num,
                        "customer_id": c_id,
                        "account_number": acc_num,
                        "incident_type": inc_type,
                        "amount_involved": float(amount),
                        "recovered_amount": float(rec_amt or 0.0),
                        "severity": sev,
                        "status": st,
                        "incident_date": str(inc_date),
                        "description": desc
                    }
                )

                # Edge: Customer -> Ticket
                if cust_node in g:
                    g.add_edge(cust_node, t_node, key="REPORTED_TICKET", relationship="REPORTED_TICKET", label="reported")
                
                # Edge: Ticket -> Account
                if acc_node in g:
                    g.add_edge(t_node, acc_node, key="INVOLVES_ACCOUNT", relationship="INVOLVES_ACCOUNT", label="involves")

                # Node & Edge: Suspect Entity (Merchant / UPI / Mule Account)
                if suspect and suspect.strip() not in ("", "Unknown", "Flagged Merchant / Beneficiary"):
                    susp_clean = suspect.strip()
                    susp_node = f"SUSP_{susp_clean.lower().replace(' ', '_')}"
                    
                    if susp_node not in g:
                        g.add_node(
                            susp_node,
                            node_type="SUSPECT",
                            label=susp_clean,
                            title=f"<b>🚨 Suspect Entity / Hub:</b><br>{susp_clean}<br><i>Potential Fraud Syndicate / Scammer UPI</i>",
                            details={"suspect_name": susp_clean}
                        )
                    
                    g.add_edge(
                        t_node, 
                        susp_node, 
                        key=f"TRANSFERRED_TO_{t_id}", 
                        relationship="TRANSFERRED_TO", 
                        label=f"₹{float(amount):,.0f}",
                        amount=float(amount)
                    )

                # Node & Edge: Flagged IP / Location
                if ip_loc and ip_loc.strip() not in ("", "127.0.0.1", "Web Client Terminal", "Unknown"):
                    ip_clean = ip_loc.strip()
                    ip_node = f"IP_{ip_clean.replace(' ', '_')}"
                    if ip_node not in g:
                        g.add_node(
                            ip_node,
                            node_type="IP_LOCATION",
                            label=ip_clean,
                            title=f"<b>Flagged Location / IP:</b><br>{ip_clean}",
                            details={"location": ip_clean}
                        )
                    g.add_edge(t_node, ip_node, key=f"LOGGED_FROM_{t_id}", relationship="LOGGED_FROM", label="origin")

                # Node & Edge: Investigator
                if inv and inv.strip():
                    inv_clean = inv.split("(")[0].strip()
                    inv_node = f"INV_{inv_clean.replace(' ', '_')}"
                    if inv_node not in g:
                        g.add_node(
                            inv_node,
                            node_type="INVESTIGATOR",
                            label=inv_clean,
                            title=f"<b>Investigator:</b><br>{inv}",
                            details={"name": inv}
                        )
                    g.add_edge(t_node, inv_node, key=f"ASSIGNED_TO_{t_id}", relationship="ASSIGNED_TO", label="assigned")

            self.graph = g
            self.last_built_at = time.time()
            logger.info(f"Knowledge Graph updated: {g.number_of_nodes()} nodes, {g.number_of_edges()} edges.")
            return self.graph
        finally:
            cursor.close()
            conn.close()

    def get_graph(self) -> nx.MultiDiGraph:
        """Returns the active graph, rebuilding if empty or older than 60s."""
        if not self.graph or (time.time() - self.last_built_at > 60):
            return self.refresh_from_postgres()
        return self.graph

    def to_visjs_format(self, subgraph: Optional[nx.MultiDiGraph] = None) -> Dict[str, Any]:
        """Convert NetworkX graph into Vis.js DataSet format with colors and styles."""
        g = subgraph if subgraph is not None else self.get_graph()
        
        vis_nodes = []
        vis_edges = []

        for node_id, data in g.nodes(data=True):
            ntype = data.get("node_type", "CUSTOMER")
            style = NODE_STYLES.get(ntype, NODE_STYLES["CUSTOMER"])
            
            # Dynamic size based on in-degree (connections)
            degree = g.degree(node_id)
            node_size = style["size"] + min(20, degree * 2)

            vis_nodes.append({
                "id": node_id,
                "label": data.get("label", node_id),
                "group": ntype,
                "shape": style["shape"],
                "color": style["color"],
                "size": node_size,
                "title": data.get("title", f"<b>{node_id}</b>"),
                "font": style["font"],
                "details": data.get("details", {})
            })

        for u, v, k, data in g.edges(keys=True, data=True):
            rel = data.get("relationship", "CONNECTED_TO")
            edge_color = "#ef4444" if rel == "TRANSFERRED_TO" else ("#0284c7" if rel == "OWNS_ACCOUNT" else "#64748b")
            
            vis_edges.append({
                "from": u,
                "to": v,
                "id": f"{u}_{v}_{k}",
                "label": data.get("label", rel),
                "relation": rel,
                "color": {"color": edge_color, "highlight": "#38bdf8"},
                "arrows": "to",
                "font": {"color": "#94a3b8", "size": 10, "align": "middle", "strokeWidth": 0}
            })

        return {
            "total_nodes": len(vis_nodes),
            "total_edges": len(vis_edges),
            "nodes": vis_nodes,
            "edges": vis_edges
        }

    def get_neighborhood_subgraph(self, target_id: str, hops: int = 2) -> Dict[str, Any]:
        """Extract k-hop ego network around a specific node (e.g. customer, ticket, suspect)."""
        g = self.get_graph()
        
        # Match target_id flexibly (e.g. '105' -> 'TICK_105' or 'FRD-2026-9081' -> match label)
        matched_node = None
        if target_id in g:
            matched_node = target_id
        else:
            for n, d in g.nodes(data=True):
                if n.endswith(f"_{target_id}") or d.get("label") == target_id:
                    matched_node = n
                    break
        
        if not matched_node:
            return {"total_nodes": 0, "total_edges": 0, "nodes": [], "edges": [], "matched": False}

        # Ego graph traversal
        nodes_in_hop = {matched_node}
        current_layer = {matched_node}

        undirected = g.to_undirected(as_view=True)
        for _ in range(hops):
            next_layer = set()
            for node in current_layer:
                neighbors = set(undirected.neighbors(node))
                next_layer.update(neighbors)
            nodes_in_hop.update(next_layer)
            current_layer = next_layer

        sub_g = g.subgraph(nodes_in_hop).copy()
        return self.to_visjs_format(sub_g)

    def detect_fraud_syndicates(self) -> List[Dict[str, Any]]:
        """
        Graph Analytics Algorithm: Identifies multi-victim fraud syndicates and mule networks
        by discovering suspect nodes with in-degree > 1 or shared IP/phone infrastructure.
        """
        g = self.get_graph()
        syndicates = []

        for node_id, data in g.nodes(data=True):
            if data.get("node_type") == "SUSPECT":
                # Find all tickets transferring money to this suspect
                in_edges = [
                    (u, v, d) for u, v, d in g.in_edges(node_id, data=True) 
                    if d.get("relationship") == "TRANSFERRED_TO"
                ]

                if len(in_edges) >= 2:  # 2 or more separate complaints = Organized Syndicate
                    connected_tickets = []
                    connected_victims = set()
                    total_amount = 0.0

                    for u, v, d in in_edges:
                        ticket_data = g.nodes[u].get("details", {})
                        t_num = ticket_data.get("ticket_number", u)
                        amt = float(d.get("amount", ticket_data.get("amount_involved", 0.0)))
                        total_amount += amt

                        # Find victim customer for this ticket
                        for pred in g.predecessors(u):
                            if g.nodes[pred].get("node_type") == "CUSTOMER":
                                cust_name = g.nodes[pred].get("label", pred)
                                connected_victims.add(cust_name)

                        connected_tickets.append({
                            "ticket_number": t_num,
                            "amount": amt,
                            "severity": ticket_data.get("severity", "HIGH"),
                            "incident_type": ticket_data.get("incident_type", "Scam")
                        })

                    syndicates.append({
                        "suspect_entity": data.get("label"),
                        "suspect_node_id": node_id,
                        "victim_count": len(connected_victims),
                        "victims": list(connected_victims),
                        "tickets_count": len(connected_tickets),
                        "tickets": connected_tickets,
                        "total_exposure_inr": total_amount,
                        "risk_level": "CRITICAL" if total_amount >= 100000.0 or len(connected_victims) >= 3 else "HIGH"
                    })

        # Sort by total financial exposure descending
        syndicates.sort(key=lambda s: s["total_exposure_inr"], reverse=True)
        return syndicates

# Singleton instance
knowledge_graph_engine = FraudKnowledgeGraph()
