"""Encryption used by official enc_* KMBox packets."""

from __future__ import annotations

import struct


def derive_key_from_uuid(uuid: str) -> bytes:
    mac = bytes.fromhex(uuid)
    if len(mac) != 4:
        raise ValueError("UUID must be exactly 8 hex characters")
    return mac + b"\x00" * 12


def encrypt_packet(packet: bytes, key: bytes) -> bytes:
    """Encrypt a 128-byte packet using the official XXTEA-like routine."""
    if len(packet) != 128:
        raise ValueError("Encrypted KMBox packet must be exactly 128 bytes")
    if len(key) != 16:
        raise ValueError("KMBox encryption key must be exactly 16 bytes")

    words = list(struct.unpack("<32I", packet))
    k = struct.unpack("<4I", key)
    z = words[31]
    total = 0

    for _ in range(6):
        total = (total + 2654435769) & 0xFFFFFFFF
        e = (total >> 2) & 3
        for p in range(31):
            y = words[p + 1]
            words[p] = (
                words[p]
                + (((z >> 5) ^ (y << 2)) + ((y >> 3) ^ (z << 4)) ^ (total ^ y) + (k[(p & 3) ^ e] ^ z))
            ) & 0xFFFFFFFF
            z = words[p]
        y = words[0]
        words[31] = (
            words[31]
            + (((z >> 5) ^ (y << 2)) + ((y >> 3) ^ (z << 4)) ^ (total ^ y) + (k[(31 & 3) ^ e] ^ z))
        ) & 0xFFFFFFFF
        z = words[31]

    return struct.pack("<32I", *words)
