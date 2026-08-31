def test_send_api_contract_paths():
    assert '/confirm' in '/api/v1/reply-drafts/{reply_id}/confirm' and '/send' in '/api/v1/reply-drafts/{reply_id}/send'
