def invalidate_after_edit(draft):
    draft.version += 1; draft.checks = []; draft.reply = None; draft.status = "READY_FOR_CHECK"; return draft
