from fed_dp_lp.systems import logical_payload_bytes, peak_resident_memory_bytes


def test_logical_payload_bytes_are_explicit_float64_counts():
    assert logical_payload_bytes(clients=5, dimension=136) == {
        "client_payload_bytes": 5440,
        "server_release_bytes": 1088,
    }


def test_peak_resident_memory_is_positive():
    assert peak_resident_memory_bytes() > 0
