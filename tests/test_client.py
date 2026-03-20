import struct
from unittest.mock import patch

from kmbox_universal import HidKey, KMBoxClient
from kmbox_universal.commands import CMD_CONNECT, CMD_KEYBOARD_ALL, CMD_MOUSE_AUTOMOVE, CMD_MOUSE_MOVE


class FakeSocket:
    def __init__(self):
        self.sent = []
        self.timeout = None
        self.server = None

    def settimeout(self, value):
        self.timeout = value

    def sendto(self, data, server):
        self.sent.append((data, server))
        self.server = server

    def recvfrom(self, _size):
        last_data, server = self.sent[-1]
        header = last_data[:16]
        return header, server

    def close(self):
        return None


def make_client():
    sock = FakeSocket()
    client = KMBoxClient("192.168.2.188", 6314, "39EBDC32", socket_factory=lambda: sock)
    return client, sock


def test_connect_sends_connect_header():
    client, sock = make_client()
    cmd = struct.unpack("<IIII", sock.sent[0][0][:16])[3]
    assert cmd == CMD_CONNECT
    client.close()


def test_move_auto_overrides_rand_with_duration():
    client, sock = make_client()
    client.move_auto(10, 20, 150)
    mac, rand_value, _index, cmd = struct.unpack("<IIII", sock.sent[-1][0][:16])
    assert mac == int("39EBDC32", 16)
    assert rand_value == 150
    assert cmd == CMD_MOUSE_AUTOMOVE
    client.close()


def test_key_press_sends_keyboard_command():
    client, sock = make_client()
    client.key_down(HidKey.C)
    cmd = struct.unpack("<IIII", sock.sent[-1][0][:16])[3]
    assert cmd == CMD_KEYBOARD_ALL
    client.close()


def test_move_to_homes_then_moves():
    client, sock = make_client()
    baseline = len(sock.sent)
    with patch("kmbox_universal.client.random.choice", return_value="top_left"):
        client.move_to(10, 10, duration_ms=120)
    packets = [struct.unpack("<IIII", data[:16])[3] for data, _ in sock.sent[baseline:]]
    assert packets[:4] == [CMD_MOUSE_MOVE] * 4
    assert packets[-1] == CMD_MOUSE_AUTOMOVE
    client.close()


def test_move_to_from_bottom_right_reverses_target_delta():
    client, sock = make_client()
    baseline = len(sock.sent)
    with patch("kmbox_universal.client.random.choice", return_value="bottom_right"):
        client.move_to(10, 10, duration_ms=120)

    move_packets = sock.sent[baseline:baseline + 4]
    for data, _ in move_packets:
        _mac, _rand, _index, cmd = struct.unpack("<IIII", data[:16])
        assert cmd == CMD_MOUSE_MOVE
        buttons, x, y, wheel = struct.unpack("<4i", data[16:32])
        assert (buttons, x, y, wheel) == (0, 10000, 10000, 0)

    final_data, _ = sock.sent[baseline + 4]
    _mac, rand_value, _index, cmd = struct.unpack("<IIII", final_data[:16])
    assert rand_value == 120
    assert cmd == CMD_MOUSE_AUTOMOVE
    buttons, x, y, wheel = struct.unpack("<4i", final_data[16:32])
    assert (buttons, x, y, wheel) == (0, -(2560 - 10), -(1440 - 10), 0)
    client.close()
