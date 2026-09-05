import json
import re
from pathlib import Path
from collections import Counter

from .contracts import CandidateSource, QuestionCandidate

_CORPUS: list[dict] | None = None


def load_corpus(path: str | None = None) -> list[dict]:
    global _CORPUS
    if _CORPUS is not None and path is None:
        return _CORPUS
    corpus_path = Path(path or Path(__file__).parents[3] / "data" / "seed" / "pqg_dialogues.json")
    try:
        _CORPUS = json.loads(corpus_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        _CORPUS = []
    return _CORPUS


def _tokens(text: str) -> set[str]:
    return {token for token in re.findall(r"[\u4e00-\u9fff]{2,}|[a-zA-Z0-9]+", text.lower())}


def retrieve(context: str, limit: int = 6) -> list[QuestionCandidate]:
    query = _tokens(context)
    scored: list[tuple[float, int, dict]] = []
    for item in load_corpus():
        item_tokens = _tokens(str(item.get("context", "")))
        similarity = len(query & item_tokens) / max(1, len(query | item_tokens))
        if similarity <= 0:
            continue
        scored.append((similarity, int(item.get("frequency", 1)), item))
    scored.sort(key=lambda row: (row[0], row[1]), reverse=True)
    candidates: list[QuestionCandidate] = []
    seen: set[str] = set()
    for similarity, frequency, item in scored:
        text = str(item.get("followup", "")).strip()
        key = re.sub(r"\W", "", text).lower()
        if not text or key in seen:
            continue
        seen.add(key)
        candidates.append(QuestionCandidate(
            candidate_id=f"retrieval-{len(candidates)+1}", text=text,
            source=CandidateSource.RETRIEVAL,
            relevance_score=round(similarity, 3),
            confidence=min(1, round(similarity * 0.7 + min(frequency, 10) / 30, 3)),
            rank=len(candidates) + 1,
            evidence_ids=[str(item.get("id", "history"))],
        ))
        if len(candidates) >= limit:
            break
    return candidates
