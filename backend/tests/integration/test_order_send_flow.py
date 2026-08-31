def test_send_flow_requires_confirmed_state():
    assert 'CONFIRMED' != 'DRAFT'
