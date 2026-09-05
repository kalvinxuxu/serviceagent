import inspect

from backend.app.agent import planner


def test_planner_module_does_not_import_tool_registry_or_domain_execution():
    source = inspect.getsource(planner)
    assert "tools.registry" not in source
    assert "domain_service.execute" not in source
