"""Shared datatypes and HID tables."""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from enum import IntEnum, IntFlag


class HidKey(IntEnum):
    NONE = 0x00
    A = 0x04
    B = 0x05
    C = 0x06
    D = 0x07
    E = 0x08
    F = 0x09
    G = 0x0A
    H = 0x0B
    I = 0x0C
    J = 0x0D
    K = 0x0E
    L = 0x0F
    M = 0x10
    N = 0x11
    O = 0x12
    P = 0x13
    Q = 0x14
    R = 0x15
    S = 0x16
    T = 0x17
    U = 0x18
    V = 0x19
    W = 0x1A
    X = 0x1B
    Y = 0x1C
    Z = 0x1D
    NUM1 = 0x1E
    NUM2 = 0x1F
    NUM3 = 0x20
    NUM4 = 0x21
    NUM5 = 0x22
    NUM6 = 0x23
    NUM7 = 0x24
    NUM8 = 0x25
    NUM9 = 0x26
    NUM0 = 0x27
    ENTER = 0x28
    ESCAPE = 0x29
    BACKSPACE = 0x2A
    TAB = 0x2B
    SPACE = 0x2C
    MINUS = 0x2D
    EQUAL = 0x2E
    LBRACKET = 0x2F
    RBRACKET = 0x30
    BACKSLASH = 0x31
    SEMICOLON = 0x33
    QUOTE = 0x34
    GRAVE = 0x35
    COMMA = 0x36
    PERIOD = 0x37
    SLASH = 0x38
    CAPS_LOCK = 0x39
    F1 = 0x3A
    F2 = 0x3B
    F3 = 0x3C
    F4 = 0x3D
    F5 = 0x3E
    F6 = 0x3F
    F7 = 0x40
    F8 = 0x41
    F9 = 0x42
    F10 = 0x43
    F11 = 0x44
    F12 = 0x45
    PRINT_SCREEN = 0x46
    SCROLL_LOCK = 0x47
    PAUSE = 0x48
    INSERT = 0x49
    HOME = 0x4A
    PAGE_UP = 0x4B
    DELETE = 0x4C
    END = 0x4D
    PAGE_DOWN = 0x4E
    RIGHT = 0x4F
    LEFT = 0x50
    DOWN = 0x51
    UP = 0x52
    LEFT_CTRL = 0xE0
    LEFT_SHIFT = 0xE1
    LEFT_ALT = 0xE2
    LEFT_GUI = 0xE3
    RIGHT_CTRL = 0xE4
    RIGHT_SHIFT = 0xE5
    RIGHT_ALT = 0xE6
    RIGHT_GUI = 0xE7


class MouseButton(IntFlag):
    LEFT = 0x01
    RIGHT = 0x02
    MIDDLE = 0x04
    SIDE1 = 0x08
    SIDE2 = 0x10


class KeyboardModifier(IntFlag):
    LEFT_CTRL = 0x01
    LEFT_SHIFT = 0x02
    LEFT_ALT = 0x04
    LEFT_GUI = 0x08
    RIGHT_CTRL = 0x10
    RIGHT_SHIFT = 0x20
    RIGHT_ALT = 0x40
    RIGHT_GUI = 0x80


@dataclass(slots=True)
class CmdHead:
    mac: int
    rand: int
    index: int
    cmd: int

    def to_bytes(self) -> bytes:
        return struct.pack("<IIII", self.mac, self.rand & 0xFFFFFFFF, self.index, self.cmd)


@dataclass(slots=True)
class SoftMouse:
    buttons: int = 0
    x: int = 0
    y: int = 0
    wheel: int = 0
    points: list[int] = field(default_factory=lambda: [0] * 10)

    def to_bytes(self) -> bytes:
        return struct.pack("<14i", self.buttons, self.x, self.y, self.wheel, *self.points)

    def reset_motion(self) -> None:
        self.x = 0
        self.y = 0
        self.wheel = 0
        self.points = [0] * 10


@dataclass(slots=True)
class SoftKeyboard:
    modifiers: int = 0
    reserved: int = 0
    buttons: list[int] = field(default_factory=lambda: [0] * 10)

    def to_bytes(self) -> bytes:
        return struct.pack("<BB10B", self.modifiers, self.reserved, *self.buttons)


@dataclass(slots=True)
class MouseReport:
    report_id: int = 0
    buttons: int = 0
    x: int = 0
    y: int = 0
    wheel: int = 0


@dataclass(slots=True)
class KeyboardReport:
    report_id: int = 0
    modifiers: int = 0
    buttons: list[int] = field(default_factory=lambda: [0] * 10)


CHAR_TO_KEY: dict[str, tuple[HidKey, KeyboardModifier]] = {
    **{chr(ord("a") + i): (HidKey(0x04 + i), KeyboardModifier(0)) for i in range(26)},
    **{chr(ord("A") + i): (HidKey(0x04 + i), KeyboardModifier.LEFT_SHIFT) for i in range(26)},
    **{str(i): (HidKey(0x1E + i - 1), KeyboardModifier(0)) for i in range(1, 10)},
    "0": (HidKey.NUM0, KeyboardModifier(0)),
    " ": (HidKey.SPACE, KeyboardModifier(0)),
    "\n": (HidKey.ENTER, KeyboardModifier(0)),
    ".": (HidKey.PERIOD, KeyboardModifier(0)),
    ",": (HidKey.COMMA, KeyboardModifier(0)),
    "/": (HidKey.SLASH, KeyboardModifier(0)),
    "-": (HidKey.MINUS, KeyboardModifier(0)),
    "=": (HidKey.EQUAL, KeyboardModifier(0)),
    ";": (HidKey.SEMICOLON, KeyboardModifier(0)),
    "'": (HidKey.QUOTE, KeyboardModifier(0)),
    "[": (HidKey.LBRACKET, KeyboardModifier(0)),
    "]": (HidKey.RBRACKET, KeyboardModifier(0)),
    "\\": (HidKey.BACKSLASH, KeyboardModifier(0)),
    "!": (HidKey.NUM1, KeyboardModifier.LEFT_SHIFT),
    "@": (HidKey.NUM2, KeyboardModifier.LEFT_SHIFT),
    "#": (HidKey.NUM3, KeyboardModifier.LEFT_SHIFT),
    "$": (HidKey.NUM4, KeyboardModifier.LEFT_SHIFT),
    "%": (HidKey.NUM5, KeyboardModifier.LEFT_SHIFT),
    "^": (HidKey.NUM6, KeyboardModifier.LEFT_SHIFT),
    "&": (HidKey.NUM7, KeyboardModifier.LEFT_SHIFT),
    "*": (HidKey.NUM8, KeyboardModifier.LEFT_SHIFT),
    "(": (HidKey.NUM9, KeyboardModifier.LEFT_SHIFT),
    ")": (HidKey.NUM0, KeyboardModifier.LEFT_SHIFT),
    "_": (HidKey.MINUS, KeyboardModifier.LEFT_SHIFT),
    "+": (HidKey.EQUAL, KeyboardModifier.LEFT_SHIFT),
    ":": (HidKey.SEMICOLON, KeyboardModifier.LEFT_SHIFT),
    "\"": (HidKey.QUOTE, KeyboardModifier.LEFT_SHIFT),
    "<": (HidKey.COMMA, KeyboardModifier.LEFT_SHIFT),
    ">": (HidKey.PERIOD, KeyboardModifier.LEFT_SHIFT),
    "?": (HidKey.SLASH, KeyboardModifier.LEFT_SHIFT),
}
