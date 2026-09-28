"""
Customer_GraphAPI - Configuration Module
"""

import os

# Server settings
GRAPH_SERVER_HOST = os.getenv("GRAPH_SERVER_HOST", "0.0.0.0")
GRAPH_SERVER_PORT = int(os.getenv("GRAPH_SERVER_PORT", "8181"))

# Database settings (PostgreSQL bank_fraud_portal)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "root")
DB_NAME = os.getenv("DB_NAME", "bank_fraud_portal")

# OpenAI LLM Key (Optional)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
