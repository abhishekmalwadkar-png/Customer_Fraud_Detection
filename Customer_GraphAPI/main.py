"""
Customer_GraphAPI - FastAPI Graph Engine & LangGraph Agent Gateway
Interactive Swagger UI available at /docs.
"""

import os
import time
import logging
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from config import GRAPH_SERVER_HOST, GRAPH_SERVER_PORT, DB_NAME, DB_HOST, DB_PORT
from graph_engine import knowledge_graph_engine
from langgraph_agent import langgraph_fraud_agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [Customer_GraphAPI] %(message)s'
)
logger = logging.getLogger("Customer_GraphAPI")

# Initialize FastAPI app
app = FastAPI(
    title="Customer_GraphAPI - Fraud Knowledge Graph & LangGraph Agent Gateway",
    description="Enterprise Graph RAG API powered by NetworkX, LangGraph, and PostgreSQL. Visualizes multi-hop fraud networks and executes autonomous agentic forensic investigations.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Global CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# -------------------------------------------------------------
# Request Schemas
# -------------------------------------------------------------
class InvestigateRequestSchema(BaseModel):
    ticket_query: str = Field(..., description="Ticket ID, Ticket Number, or Customer Name to investigate", examples=["FRD-2026-9081"])

# -------------------------------------------------------------
# Static Dashboard Route
# -------------------------------------------------------------
@app.get("/", include_in_schema=False)
async def serve_dashboard():
    index_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    return HTMLResponse("<h2>Customer_GraphAPI Server is Online. Visit /docs for API documentation.</h2>")

# -------------------------------------------------------------
# Health & Diagnostics
# -------------------------------------------------------------
@app.get("/health", tags=["Observability"])
def health_check():
    """System health check and PostgreSQL live connectivity diagnostic."""
    t0 = time.time()
    db_ok = False
    try:
        conn = knowledge_graph_engine.get_db_connection()
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.fetchone()
        cur.close()
        conn.close()
        db_ok = True
    except Exception as e:
        logger.error(f"Health DB ping error: {e}")

    return {
        "status": "UP" if db_ok else "DEGRADED",
        "service": "Customer_GraphAPI (LangGraph + NetworkX Engine)",
        "database": {
            "name": DB_NAME,
            "host": f"{DB_HOST}:{DB_PORT}",
            "status": "CONNECTED" if db_ok else "DISCONNECTED",
            "latency_ms": round((time.time() - t0) * 1000, 2)
        },
        "server_time": time.strftime("%Y-%m-%d %H:%M:%S UTC")
    }

# -------------------------------------------------------------
# Graph RAG & Knowledge Graph Endpoints
# -------------------------------------------------------------
@app.get("/api/graph/network", tags=["Knowledge Graph"])
def get_full_fraud_network(refresh: bool = False):
    """
    Returns the complete Knowledge Graph (Nodes, Edges, Colors, and Attributes)
    ready for Vis.js or Cytoscape.js rendering.
    """
    if refresh:
        knowledge_graph_engine.refresh_from_postgres()
    return knowledge_graph_engine.to_visjs_format()


@app.get("/api/graph/subgraph/{entity_id}", tags=["Knowledge Graph"])
def get_entity_subgraph(entity_id: str, hops: int = 2):
    """
    Extracts a focused 1-hop or 2-hop neighborhood ego-graph centered on a specific
    Customer ID, Ticket Number, or Suspect Entity.
    """
    subgraph = knowledge_graph_engine.get_neighborhood_subgraph(entity_id, hops=hops)
    if subgraph["total_nodes"] == 0:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found in Knowledge Graph.")
    return subgraph


@app.get("/api/graph/syndicates", tags=["Fraud Analytics"])
def get_fraud_syndicates():
    """
    Discovers all multi-victim fraud syndicates and mule accounts across the graph.
    """
    syndicates = knowledge_graph_engine.detect_fraud_syndicates()
    return {
        "total_syndicates_detected": len(syndicates),
        "total_at_risk_inr": sum(s["total_exposure_inr"] for s in syndicates),
        "syndicates": syndicates
    }

# -------------------------------------------------------------
# LangGraph Agentic Investigation Endpoints
# -------------------------------------------------------------
@app.post("/api/agent/investigate", tags=["LangGraph Multi-Agent"])
def run_langgraph_investigation(payload: InvestigateRequestSchema):
    """
    Executes the LangGraph Multi-Agent Forensic Workflow:
    1. Data Ingestion -> 2. Graph RAG Extraction -> 3. Syndicate Detection ->
    4. Risk Reasoning -> 5. Emergency Mitigation -> 6. Final Dossier Compilation.
    """
    try:
        result = langgraph_fraud_agent.execute(payload.ticket_query)
        return {
            "success": True,
            "ticket_number": result["ticket_data"].get("ticket_number"),
            "customer_name": result["ticket_data"].get("customer_name"),
            "risk_score": result["risk_score"],
            "risk_level": result["risk_level"],
            "is_syndicate": result["is_syndicate"],
            "syndicate_details": result["syndicate_details"],
            "mitigation_actions": result["mitigation_actions"],
            "step_traces": result["step_traces"],
            "forensic_report": result["forensic_report"]
        }
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"LangGraph execution error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agent/runs", tags=["LangGraph Multi-Agent"])
def get_langgraph_run_history():
    """
    Retrieves the execution history of all LangGraph investigations run during this session.
    """
    return {
        "total_runs": len(langgraph_fraud_agent.workflow_history),
        "runs": langgraph_fraud_agent.workflow_history
    }

# -------------------------------------------------------------
# Main Entry Point
# -------------------------------------------------------------
if __name__ == "__main__":
    print("\n=======================================================")
    print("[+] Customer_GraphAPI (LangGraph + Graph RAG Engine)")
    print(f"[*] Interactive UI: http://localhost:{GRAPH_SERVER_PORT}")
    print(f"[*] Swagger Docs:   http://localhost:{GRAPH_SERVER_PORT}/docs")
    print("=======================================================\n")
    uvicorn.run("main:app", host=GRAPH_SERVER_HOST, port=GRAPH_SERVER_PORT, reload=True)
