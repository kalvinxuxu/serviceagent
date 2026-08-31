from evals.runner import success_criteria


def test_success_criteria_runner_passes_all_gates():
    report = success_criteria()
    assert report["all_passed"] is True
