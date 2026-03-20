from kmbox_universal.crypto import derive_key_from_uuid, encrypt_packet


def test_derive_key_from_uuid():
    assert derive_key_from_uuid("39EBDC32") == bytes.fromhex("39EBDC32") + b"\x00" * 12


def test_encrypt_packet_length():
    packet = bytes(range(128))
    key = bytes.fromhex("39EBDC32") + b"\x00" * 12
    encrypted = encrypt_packet(packet, key)
    assert len(encrypted) == 128
    assert encrypted != packet
