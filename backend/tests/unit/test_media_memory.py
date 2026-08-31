from backend.app.domain.memory_service import validate_candidate
from backend.app.domain.media_service import list_media


def test_memory_requires_explicit_signal():
    ok, reason = validate_candidate({"type": "EXPLICIT_PREFERENCE", "key": "texture", "value": "SOFT"})
    assert not ok
    assert reason == "MEMORY_REQUIRES_EXPLICIT_USER_SIGNAL"


def test_observed_behavior_is_allowed_as_weak_signal():
    ok, reason = validate_candidate({"type": "OBSERVED_BEHAVIOR", "key": "category", "value": "贝果"})
    assert ok
    assert reason is None


def test_featured_board_media_is_registered():
    assert any(item["type"] == "FEATURED_BOARD" for item in list_media())
