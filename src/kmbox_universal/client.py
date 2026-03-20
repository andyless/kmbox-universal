"""Public KMBox Net client."""

from __future__ import annotations

import ipaddress
import random
import socket
import struct
import time
from dataclasses import dataclass
from typing import Callable

from . import commands
from .crypto import derive_key_from_uuid, encrypt_packet
from .exceptions import KMBoxProtocolError, KMBoxTimeoutError
from .monitor import MonitorListener
from .types import CHAR_TO_KEY, CmdHead, HidKey, KeyboardModifier, MouseButton, SoftKeyboard, SoftMouse


@dataclass(slots=True)
class AbsoluteMouseConfig:
    mode: str = "corner_random"
    home_step: int = 10000
    home_repeat: int = 4
    settle_ms: int = 20
    move_duration_ms: int = 160
    screen_width: int = 2560
    screen_height: int = 1440


class KMBoxClient:
    def __init__(
        self,
        host: str,
        port: int,
        uuid: str,
        *,
        timeout: float = 2.0,
        auto_connect: bool = True,
        absolute_mouse: AbsoluteMouseConfig | None = None,
        socket_factory: Callable[[], socket.socket] | None = None,
    ):
        self.host = host
        self.port = port
        self.uuid = uuid.upper()
        self.timeout = timeout
        self.absolute_mouse = absolute_mouse or AbsoluteMouseConfig()
        self._socket_factory = socket_factory or (lambda: socket.socket(socket.AF_INET, socket.SOCK_DGRAM))
        self._sock = self._socket_factory()
        self._sock.settimeout(timeout)
        self._server = (host, port)
        self._mac = int.from_bytes(bytes.fromhex(self.uuid), byteorder="big")
        self._index = 0
        self._mouse = SoftMouse()
        self._keyboard = SoftKeyboard()
        self._mask_flag = 0
        self._enc_key = derive_key_from_uuid(self.uuid)
        self.monitor: MonitorListener | None = None
        if auto_connect:
            self.connect()

    def connect(self) -> bool:
        self._index = 0
        self._send_head(commands.CMD_CONNECT)
        return True

    def close(self) -> None:
        if self.monitor is not None:
            self.monitor.stop()
            self.monitor = None
        self._sock.close()

    def _next_head(self, cmd: int, rand_override: int | None = None) -> CmdHead:
        self._index += 1
        rand_value = rand_override if rand_override is not None else random.randint(0, 0x7FFFFFFF)
        return CmdHead(self._mac, rand_value, self._index, cmd)

    def _recv_validate(self, expected: CmdHead, *, strict: bool = True) -> bytes:
        try:
            payload, sender = self._sock.recvfrom(65535)
        except socket.timeout as exc:
            raise KMBoxTimeoutError("KMBox did not reply before timeout") from exc
        if sender != self._server:
            raise KMBoxProtocolError(f"Unexpected sender {sender}, expected {self._server}")
        if len(payload) < 16:
            raise KMBoxProtocolError("Response shorter than KMBox header")
        mac, rand_value, index, cmd = struct.unpack("<IIII", payload[:16])
        if strict and (cmd != expected.cmd or index != expected.index):
            raise KMBoxProtocolError(
                f"Response mismatch: cmd={cmd:#x} index={index}, expected cmd={expected.cmd:#x} index={expected.index}"
            )
        return payload

    def _send(self, cmd: int, payload: bytes = b"", *, rand_override: int | None = None, strict: bool = True) -> bytes:
        head = self._next_head(cmd, rand_override)
        packet = head.to_bytes() + payload
        self._sock.sendto(packet, self._server)
        return self._recv_validate(head, strict=strict)

    def _send_encrypted(self, cmd: int, payload: bytes = b"", *, rand_override: int | None = None) -> bytes:
        head = self._next_head(cmd, rand_override)
        raw = head.to_bytes() + payload
        padded = raw.ljust(128, b"\x00")
        self._sock.sendto(encrypt_packet(padded, self._enc_key), self._server)
        return self._recv_validate(head, strict=False)

    def _send_head(self, cmd: int, *, rand_override: int | None = None, strict: bool = True) -> bytes:
        return self._send(cmd, b"", rand_override=rand_override, strict=strict)

    def move(self, dx: int, dy: int) -> bool:
        self._mouse.x = dx
        self._mouse.y = dy
        self._send(commands.CMD_MOUSE_MOVE, self._mouse.to_bytes())
        self._mouse.reset_motion()
        return True

    def enc_move(self, dx: int, dy: int) -> bool:
        self._mouse.x = dx
        self._mouse.y = dy
        self._send_encrypted(commands.CMD_MOUSE_MOVE, self._mouse.to_bytes())
        self._mouse.reset_motion()
        return True

    def move_auto(self, dx: int, dy: int, duration_ms: int) -> bool:
        self._mouse.x = dx
        self._mouse.y = dy
        self._send(commands.CMD_MOUSE_AUTOMOVE, self._mouse.to_bytes(), rand_override=duration_ms)
        self._mouse.reset_motion()
        return True

    def enc_move_auto(self, dx: int, dy: int, duration_ms: int) -> bool:
        self._mouse.x = dx
        self._mouse.y = dy
        self._send_encrypted(commands.CMD_MOUSE_AUTOMOVE, self._mouse.to_bytes(), rand_override=duration_ms)
        self._mouse.reset_motion()
        return True

    def move_bezier(self, dx: int, dy: int, duration_ms: int, x1: int, y1: int, x2: int, y2: int) -> bool:
        self._mouse.x = dx
        self._mouse.y = dy
        self._mouse.points[0:4] = [x1, y1, x2, y2]
        self._send(commands.CMD_BEZIER_MOVE, self._mouse.to_bytes(), rand_override=duration_ms)
        self._mouse.reset_motion()
        return True

    def enc_move_bezier(self, dx: int, dy: int, duration_ms: int, x1: int, y1: int, x2: int, y2: int) -> bool:
        self._mouse.x = dx
        self._mouse.y = dy
        self._mouse.points[0:4] = [x1, y1, x2, y2]
        self._send_encrypted(commands.CMD_BEZIER_MOVE, self._mouse.to_bytes(), rand_override=duration_ms)
        self._mouse.reset_motion()
        return True

    def _button_mask(self, button: MouseButton | str | int) -> int:
        if isinstance(button, int):
            return button
        if isinstance(button, MouseButton):
            return int(button)
        return int(MouseButton[button.upper()])

    def _button_cmd(self, button_mask: int) -> int:
        if button_mask == int(MouseButton.LEFT):
            return commands.CMD_MOUSE_LEFT
        if button_mask == int(MouseButton.RIGHT):
            return commands.CMD_MOUSE_RIGHT
        if button_mask == int(MouseButton.MIDDLE):
            return commands.CMD_MOUSE_MIDDLE
        return commands.CMD_MOUSE_LEFT

    def button(self, button: MouseButton | str | int, is_down: bool) -> bool:
        mask = self._button_mask(button)
        self._mouse.buttons = self._mouse.buttons | mask if is_down else self._mouse.buttons & ~mask
        self._send(self._button_cmd(mask), self._mouse.to_bytes())
        return True

    def enc_button(self, button: MouseButton | str | int, is_down: bool) -> bool:
        mask = self._button_mask(button)
        self._mouse.buttons = self._mouse.buttons | mask if is_down else self._mouse.buttons & ~mask
        self._send_encrypted(self._button_cmd(mask), self._mouse.to_bytes())
        return True

    def left(self, is_down: bool) -> bool:
        return self.button(MouseButton.LEFT, is_down)

    def right(self, is_down: bool) -> bool:
        return self.button(MouseButton.RIGHT, is_down)

    def middle(self, is_down: bool) -> bool:
        return self.button(MouseButton.MIDDLE, is_down)

    def side1(self, is_down: bool) -> bool:
        return self.button(MouseButton.SIDE1, is_down)

    def side2(self, is_down: bool) -> bool:
        return self.button(MouseButton.SIDE2, is_down)

    def enc_left(self, is_down: bool) -> bool:
        return self.enc_button(MouseButton.LEFT, is_down)

    def enc_right(self, is_down: bool) -> bool:
        return self.enc_button(MouseButton.RIGHT, is_down)

    def enc_middle(self, is_down: bool) -> bool:
        return self.enc_button(MouseButton.MIDDLE, is_down)

    def enc_side1(self, is_down: bool) -> bool:
        return self.enc_button(MouseButton.SIDE1, is_down)

    def enc_side2(self, is_down: bool) -> bool:
        return self.enc_button(MouseButton.SIDE2, is_down)

    def click(self, button: MouseButton | str | int = MouseButton.LEFT, duration_ms: int = 50) -> bool:
        self.button(button, True)
        time.sleep(duration_ms / 1000.0)
        self.button(button, False)
        return True

    def wheel(self, amount: int) -> bool:
        self._mouse.wheel = amount
        self._send(commands.CMD_MOUSE_WHEEL, self._mouse.to_bytes())
        self._mouse.reset_motion()
        return True

    def enc_wheel(self, amount: int) -> bool:
        self._mouse.wheel = amount
        self._send_encrypted(commands.CMD_MOUSE_WHEEL, self._mouse.to_bytes())
        self._mouse.reset_motion()
        return True

    def mouse_all(self, buttons: int, dx: int, dy: int, wheel: int) -> bool:
        self._mouse.buttons = buttons
        self._mouse.x = dx
        self._mouse.y = dy
        self._mouse.wheel = wheel
        self._send(commands.CMD_MOUSE_WHEEL, self._mouse.to_bytes())
        self._mouse.reset_motion()
        return True

    def _normalize_key(self, key: HidKey | int) -> int:
        return int(key)

    def key_down(self, key: HidKey | int) -> bool:
        key_code = self._normalize_key(key)
        if 0xE0 <= key_code <= 0xE7:
            self._keyboard.modifiers |= 1 << (key_code - 0xE0)
        else:
            for idx, current in enumerate(self._keyboard.buttons):
                if current == key_code:
                    break
                if current == 0:
                    self._keyboard.buttons[idx] = key_code
                    break
            else:
                self._keyboard.buttons = self._keyboard.buttons[1:] + [key_code]
        self._send(commands.CMD_KEYBOARD_ALL, self._keyboard.to_bytes())
        return True

    def enc_key_down(self, key: HidKey | int) -> bool:
        key_code = self._normalize_key(key)
        if 0xE0 <= key_code <= 0xE7:
            self._keyboard.modifiers |= 1 << (key_code - 0xE0)
        else:
            for idx, current in enumerate(self._keyboard.buttons):
                if current == key_code:
                    break
                if current == 0:
                    self._keyboard.buttons[idx] = key_code
                    break
            else:
                self._keyboard.buttons = self._keyboard.buttons[1:] + [key_code]
        self._send_encrypted(commands.CMD_KEYBOARD_ALL, self._keyboard.to_bytes())
        return True

    def key_up(self, key: HidKey | int) -> bool:
        key_code = self._normalize_key(key)
        if 0xE0 <= key_code <= 0xE7:
            self._keyboard.modifiers &= ~(1 << (key_code - 0xE0))
        else:
            self._keyboard.buttons = [btn for btn in self._keyboard.buttons if btn != key_code]
            self._keyboard.buttons.extend([0] * (10 - len(self._keyboard.buttons)))
        self._send(commands.CMD_KEYBOARD_ALL, self._keyboard.to_bytes())
        return True

    def enc_key_up(self, key: HidKey | int) -> bool:
        key_code = self._normalize_key(key)
        if 0xE0 <= key_code <= 0xE7:
            self._keyboard.modifiers &= ~(1 << (key_code - 0xE0))
        else:
            self._keyboard.buttons = [btn for btn in self._keyboard.buttons if btn != key_code]
            self._keyboard.buttons.extend([0] * (10 - len(self._keyboard.buttons)))
        self._send_encrypted(commands.CMD_KEYBOARD_ALL, self._keyboard.to_bytes())
        return True

    def key_press(self, key: HidKey | int, duration_ms: int = 50, encrypted: bool = False) -> bool:
        if encrypted:
            self.enc_key_down(key)
            time.sleep(duration_ms / 1000.0)
            self.enc_key_up(key)
        else:
            self.key_down(key)
            time.sleep(duration_ms / 1000.0)
            self.key_up(key)
        return True

    def combo(self, keys: list[HidKey | int], duration_ms: int = 50, encrypted: bool = False) -> bool:
        down = self.enc_key_down if encrypted else self.key_down
        up = self.enc_key_up if encrypted else self.key_up
        for key in keys:
            down(key)
            time.sleep(random.uniform(0.005, 0.018))
        time.sleep(duration_ms / 1000.0)
        for key in reversed(keys):
            up(key)
            time.sleep(random.uniform(0.004, 0.015))
        return True

    def type_text(self, text: str, delay_ms: int = 80) -> bool:
        for char in text:
            if char not in CHAR_TO_KEY:
                raise ValueError(f"Unsupported character {char!r}")
            key, modifier = CHAR_TO_KEY[char]
            combo = [int(key)]
            if modifier & KeyboardModifier.LEFT_SHIFT:
                combo.insert(0, int(HidKey.LEFT_SHIFT))
            self.combo(combo, duration_ms=max(20, delay_ms // 2))
            time.sleep(delay_ms / 1000.0)
        return True

    def monitor_start(self, port: int = 5002, timeout: float = 0.003) -> bool:
        rand_override = port | (0xAA55 << 16)
        self._send_head(commands.CMD_MONITOR, rand_override=rand_override)
        self.monitor = MonitorListener(port, timeout)
        self.monitor.start()
        time.sleep(0.01)
        return True

    def monitor_stop(self) -> None:
        if self.monitor is not None:
            self.monitor.stop()
            self.monitor = None

    def isdown_left(self) -> int:
        return int(bool(self.monitor and self.monitor.is_down_mouse(int(MouseButton.LEFT))))

    def isdown_right(self) -> int:
        return int(bool(self.monitor and self.monitor.is_down_mouse(int(MouseButton.RIGHT))))

    def isdown_middle(self) -> int:
        return int(bool(self.monitor and self.monitor.is_down_mouse(int(MouseButton.MIDDLE))))

    def isdown_side1(self) -> int:
        return int(bool(self.monitor and self.monitor.is_down_mouse(int(MouseButton.SIDE1))))

    def isdown_side2(self) -> int:
        return int(bool(self.monitor and self.monitor.is_down_mouse(int(MouseButton.SIDE2))))

    def isdown_keyboard(self, key: HidKey | int) -> int:
        return int(bool(self.monitor and self.monitor.is_down_keyboard(int(key))))

    def _mask(self, bit: int, enabled: bool) -> bool:
        self._mask_flag = self._mask_flag | bit if enabled else self._mask_flag & ~bit
        self._send_head(commands.CMD_MASK_MOUSE, rand_override=self._mask_flag)
        return True

    def mask_left(self, enabled: bool) -> bool:
        return self._mask(0x01, enabled)

    def mask_right(self, enabled: bool) -> bool:
        return self._mask(0x02, enabled)

    def mask_middle(self, enabled: bool) -> bool:
        return self._mask(0x04, enabled)

    def mask_side1(self, enabled: bool) -> bool:
        return self._mask(0x08, enabled)

    def mask_side2(self, enabled: bool) -> bool:
        return self._mask(0x10, enabled)

    def mask_x(self, enabled: bool) -> bool:
        return self._mask(0x20, enabled)

    def mask_y(self, enabled: bool) -> bool:
        return self._mask(0x40, enabled)

    def mask_wheel(self, enabled: bool) -> bool:
        return self._mask(0x80, enabled)

    def mask_keyboard(self, key: HidKey | int) -> bool:
        rand_override = (self._mask_flag & 0xFF) | ((int(key) & 0xFF) << 8)
        self._send_head(commands.CMD_MASK_MOUSE, rand_override=rand_override)
        return True

    def unmask_keyboard(self, key: HidKey | int) -> bool:
        rand_override = (self._mask_flag & 0xFF) | ((int(key) & 0xFF) << 8)
        self._send_head(commands.CMD_UNMASK_ALL, rand_override=rand_override)
        return True

    def unmask_all(self) -> bool:
        self._mask_flag = 0
        self._send_head(commands.CMD_UNMASK_ALL, rand_override=0)
        return True

    def set_config(self, ip: str, port: int) -> bool:
        ip_int = int(ipaddress.IPv4Address(ip))
        payload = struct.pack(">H", port)
        self._send(commands.CMD_SETCONFIG, payload, rand_override=ip_int)
        return True

    def set_vid_pid(self, vid: int, pid: int) -> bool:
        self._send(commands.CMD_SETVIDPID, struct.pack("<HH", vid, pid))
        return True

    def reboot(self) -> bool:
        self._send_head(commands.CMD_REBOOT)
        self.close()
        return True

    def debug(self, port: int, enabled: bool) -> bool:
        self._send_head(commands.CMD_DEBUG, rand_override=port | (int(enabled) << 16))
        return True

    def trace_enable(self, enabled: bool) -> bool:
        self._send_head(commands.CMD_TRACE_ENABLE, rand_override=1 if enabled else 0)
        return True

    def lcd_color(self, rgb565: int) -> bool:
        row = struct.pack("<512H", *([rgb565] * 512))
        for y in range(40):
            self._send(commands.CMD_SHOWPIC, row, rand_override=y * 4)
        return True

    def lcd_picture_bottom(self, image_data: bytes) -> bool:
        if len(image_data) != 128 * 80 * 2:
            raise ValueError("Bottom LCD image must be exactly 128x80 RGB565")
        for y in range(20):
            row = image_data[y * 1024:(y + 1) * 1024]
            self._send(commands.CMD_SHOWPIC, row, rand_override=80 + y * 4)
        return True

    def lcd_picture(self, image_data: bytes) -> bool:
        if len(image_data) != 128 * 160 * 2:
            raise ValueError("Full LCD image must be exactly 128x160 RGB565")
        for y in range(40):
            row = image_data[y * 1024:(y + 1) * 1024]
            self._send(commands.CMD_SHOWPIC, row, rand_override=y * 4)
        return True

    def home_top_left(self) -> None:
        for _ in range(max(1, self.absolute_mouse.home_repeat)):
            self.move(-self.absolute_mouse.home_step, -self.absolute_mouse.home_step)
            time.sleep(self.absolute_mouse.settle_ms / 1000.0)

    def home_corner(self, corner: str) -> None:
        step = self.absolute_mouse.home_step
        normalized = corner.strip().lower()
        if normalized == "top_left":
            dx, dy = -step, -step
        elif normalized == "top_right":
            dx, dy = step, -step
        elif normalized == "bottom_left":
            dx, dy = -step, step
        elif normalized == "bottom_right":
            dx, dy = step, step
        else:
            raise ValueError(f"Unsupported home corner '{corner}'")

        for _ in range(max(1, self.absolute_mouse.home_repeat)):
            self.move(dx, dy)
            time.sleep(self.absolute_mouse.settle_ms / 1000.0)

    def _pick_home_corner(self) -> str:
        mode = self.absolute_mouse.mode.strip().lower()
        if mode == "top_left_only":
            return "top_left"
        if mode == "corner_random":
            return random.choice(["top_left", "top_right", "bottom_left", "bottom_right"])
        raise ValueError(f"Unsupported absolute mouse mode '{self.absolute_mouse.mode}'")

    def _target_delta_from_corner(self, x: int, y: int, corner: str) -> tuple[int, int]:
        width = self.absolute_mouse.screen_width
        height = self.absolute_mouse.screen_height
        normalized = corner.strip().lower()
        if normalized == "top_left":
            return x, y
        if normalized == "top_right":
            return -(width - x), y
        if normalized == "bottom_left":
            return x, -(height - y)
        if normalized == "bottom_right":
            return -(width - x), -(height - y)
        raise ValueError(f"Unsupported home corner '{corner}'")

    def move_to(self, x: int, y: int, duration_ms: int | None = None) -> bool:
        corner = self._pick_home_corner()
        self.home_corner(corner)
        time.sleep(self.absolute_mouse.settle_ms / 1000.0)
        dx, dy = self._target_delta_from_corner(x, y, corner)
        return self.move_auto(dx, dy, duration_ms or self.absolute_mouse.move_duration_ms)

    def click_at(self, x: int, y: int, button: MouseButton | str | int = MouseButton.LEFT, duration_ms: int = 50) -> bool:
        self.move_to(x, y)
        return self.click(button, duration_ms)
