def missing_questions(draft):
    return [f"请补充{field}" for field in draft.missing_information]
