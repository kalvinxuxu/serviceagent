import os

ORDER_EMAIL_SIMULATED = os.getenv("ORDER_EMAIL_SIMULATED", "true").lower() == "true"
ORDER_EMAIL_MAX_BODY = int(os.getenv("ORDER_EMAIL_MAX_BODY", "12000"))
