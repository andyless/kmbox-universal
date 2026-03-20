"""Monitor mode listener for KMBox Net."""

from __future__ import annotations

import socket
import struct
import threading
import time
from dataclasses import dataclass, field
from typing import Callable

from .types import KeyboardReport, MouseReport


@dataclass(slots=True)
class MonitorState:
    mouse: MouseReport = field(default_factory=MouseReport)
    keyboard: KeyboardReport = field(default_factory=KeyboardReport)
    last_event_ts: float = 0.0


class MonitorListener:
    def __init__(self, port: int, timeout: float = 0.003):
        self.port = port
        self.timeout = timeout
        self.state = MonitorState()
        self._callbacks: list[Callable[[MonitorState], None]] = []
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._sock: socket.socket | None = None
        self.running = False

    def add_callback(self, callback: Callable[[MonitorState], None]) -> None:
        self._callbacks.append(callback)

    def start(self) -> None:
        if self.running:
            return
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.settimeout(self.timeout)
        self._sock.bind(("0.0.0.0", self.port))
        self.running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self.running = False
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None
        if self._thread is not None:
            self._thread.join(timeout=1.0)

    def is_down_mouse(self, mask: int) -> bool:
        with self._lock:
            return bool(self.state.mouse.buttons & mask)

    def is_down_keyboard(self, key_code: int) -> bool:
        with self._lock:
            if 0xE0 <= key_code <= 0xE7:
                return bool(self.state.keyboard.modifiers & (1 << (key_code - 0xE0)))
            return key_code in self.state.keyboard.buttons

    def _run(self) -> None:
        assert self._sock is not None
        while self.running:
            try:
                data, _ = self._sock.recvfrom(1024)
            except socket.timeout:
                continue
            except OSError:
                break
            if len(data) < 20:
                continue
            mouse = MouseReport(*struct.unpack_from("<BBhhh", data, 0))
            k_report_id, modifiers, *buttons = struct.unpack_from("<BB10B", data, 8)
            keyboard = KeyboardReport(k_report_id, modifiers, list(buttons))
            with self._lock:
                self.state = MonitorState(mouse=mouse, keyboard=keyboard, last_event_ts=time.perf_counter())
                snapshot = self.state
            for callback in self._callbacks:
                callback(snapshot)
