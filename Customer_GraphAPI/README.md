# 🕸️ Customer_GraphAPI - Knowledge Graph & LangGraph Forensic Agent

Enterprise Graph RAG and Multi-Agent Forensic Investigation API for Banking Fraud Detection, powered by **FastAPI**, **NetworkX**, and **LangGraph**.

---

## 🌟 Key Features

1. **Dynamic Knowledge Graph (`/api/graph/network`)**:
   - Constructs a live multi-entity graph linking **Customers**, **Bank Accounts**, **Fraud Complaints**, **Suspect Entities/UPIS**, **Flagged IPs**, and **Investigators**.
   - Converts tabular PostgreSQL data into directed 2D/3D networks.

2. **Graph RAG Subgraph Extractor (`/api/graph/subgraph/{entity_id}`)**:
   - Extracts 1-hop and 2-hop ego-neighborhoods around any target entity to discover hidden relationship clusters.

3. **Syndicate & Mule Account Ring Discovery (`/api/graph/syndicates`)**:
   - Graph analytics algorithm identifying high in-degree suspect nodes with multiple connected victims and total financial risk exposure.

4. **LangGraph Forensic Multi-Agent Pipeline (`/api/agent/investigate`)**:
   - **Node 1 (Data Ingestion)**: Retrieves customer profile and ticket forensics from PostgreSQL.
   - **Node 2 (Graph RAG Topology)**: Traverses the graph to extract multi-hop entity neighborhoods.
   - **Node 3 (Syndicate Detection)**: Evaluates if suspect is part of an organized fraud syndicate.
   - **Node 4 (Risk Reasoning)**: Calculates multi-factor composite threat rating (0–100).
   - **Node 5 (Conditional Escalation)**: Routes to Emergency Action Plan or Standard Dispute Plan.
   - **Node 6 (Synthesis)**: Compiles an immutable Markdown Cyber Forensic Dossier.

5. **Interactive Vis.js Web UI**:
   - Real-time physics engine, node inspector, filter tags, and one-click LangGraph execution console.

---

## 🚀 How to Run

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Graph API Server
```bash
python main.py
```

### 3. Open in Browser
- **Interactive Graph UI:** [http://localhost:8181](http://localhost:8181)
- **Interactive Swagger API Docs:** [http://localhost:8181/docs](http://localhost:8181/docs)

---

## 📡 API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Serves Interactive Vis.js Knowledge Graph Dashboard |
| `GET` | `/api/graph/network` | Returns full nodes and directed edges |
| `GET` | `/api/graph/subgraph/{id}` | Returns 2-hop neighborhood centered on an entity |
| `GET` | `/api/graph/syndicates` | Lists detected fraud syndicates and mule networks |
| `POST` | `/api/agent/investigate` | Runs LangGraph stateful multi-agent investigation |
| `GET` | `/api/agent/runs` | Retrieves past agent execution run history |
| `GET` | `/health` | Health status and PostgreSQL latency ping |
