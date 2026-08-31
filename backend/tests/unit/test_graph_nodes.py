from backend.app.agent.graph import build_graph


def test_graph_exposes_replaceable_execution_nodes():
    node_names = set(build_graph().get_graph().nodes)
    assert {"load_context", "understand", "planner", "route", "update_state", "evaluate"}.issubset(node_names)
