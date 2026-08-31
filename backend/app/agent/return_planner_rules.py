def needs_confirmation(state) -> bool:
    return bool(state.known_facts.get("eligibility")) and not state.requires_confirmation
