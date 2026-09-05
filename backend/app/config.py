import os

AGENT_ARCHITECTURE = os.getenv("AGENT_ARCHITECTURE", "legacy").strip().lower()
if AGENT_ARCHITECTURE == "semantic":
    AGENT_ARCHITECTURE = "converged"
if AGENT_ARCHITECTURE not in {"legacy", "converged"}:
    raise ValueError("AGENT_ARCHITECTURE must be legacy or converged")

ORDER_EMAIL_SIMULATED = os.getenv("ORDER_EMAIL_SIMULATED", "true").lower() == "true"
ORDER_EMAIL_MAX_BODY = int(os.getenv("ORDER_EMAIL_MAX_BODY", "12000"))
PQG_ENABLED = os.getenv("PQG_ENABLED", "true").lower() == "true"
PQG_MAX_CANDIDATES = min(3, max(1, int(os.getenv("PQG_MAX_CANDIDATES", "3"))))
PQG_TIMEOUT_MS = int(os.getenv("PQG_TIMEOUT_MS", "2500"))
