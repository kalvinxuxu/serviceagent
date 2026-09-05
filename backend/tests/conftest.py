import os

import pytest


@pytest.fixture(autouse=True)
def isolate_runtime_environment():
    """Prevent Legacy/Converged and provider settings leaking between tests."""
    keys = ("AGENT_ARCHITECTURE", "LLM_PROVIDER", "LLM_MODEL", "BENCHMARK_SKIP_JUDGE")
    previous = {key: os.environ.get(key) for key in keys}
    # Tests must not depend on a developer's .env or consume a real provider.
    # Individual tests may override these values for provider/architecture
    # contract coverage; the original values are restored afterwards.
    os.environ["LLM_PROVIDER"] = "mock"
    os.environ["AGENT_ARCHITECTURE"] = "legacy"
    yield
    for key, value in previous.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
