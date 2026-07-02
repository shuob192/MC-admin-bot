import os
import sys

# Set required env vars before any module-level imports in agent/main.py
os.environ.setdefault("AGENT_API_KEY", "test-secret-key")
os.environ.setdefault("RCON_HOST", "localhost")
os.environ.setdefault("RCON_PORT", "25575")
os.environ.setdefault("RCON_PASSWORD", "test-password")

# Make agent/ importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agent"))
