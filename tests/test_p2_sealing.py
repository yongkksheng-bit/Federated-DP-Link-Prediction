import numpy as np
from cryptography.fernet import Fernet

from fed_dp_lp.p2_sealing import array_commitment, encrypted_npz


def test_commitments_are_keyed_and_content_bound():
    array = np.asarray([[0, 1], [2, 3]], dtype=np.int64)
    left = array_commitment(b"a" * 32, "test", array)
    right = array_commitment(b"a" * 32, "test", array.copy())
    changed = array_commitment(b"a" * 32, "test", array + 1)
    wrong_key = array_commitment(b"b" * 32, "test", array)
    assert left == right
    assert left != changed
    assert left != wrong_key


def test_sealed_npz_is_not_plaintext_and_round_trips_in_fixture():
    key = Fernet.generate_key()
    cipher = Fernet(key)
    array = np.asarray([[4, 7]], dtype=np.int64)
    token = encrypted_npz(cipher, test_positive=array)
    assert array.tobytes() not in token
