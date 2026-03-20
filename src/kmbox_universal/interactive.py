"""Interactive CLI for manual KMBox Net testing."""

from __future__ import annotations

import argparse
import shlex
import sys
import time
from typing import Callable

from .client import AbsoluteMouseConfig, KMBoxClient
from .types import CHAR_TO_KEY, HidKey, MouseButton


HELP_TEXT = """Commands:
  help
  quit | exit
  press <key> [duration_ms]
  press_enc <key> [duration_ms]
  down <key>
  up <key>
  combo <key1,key2,...> [duration_ms]
  type <text>
  move <dx> <dy>
  move_enc <dx> <dy>
  move_auto <dx> <dy> <duration_ms>
  bezier <dx> <dy> <duration_ms> <x1> <y1> <x2> <y2>
  click [left|right|middle] [duration_ms]
  click_at <x> <y> [left|right|middle] [duration_ms]
  wheel <amount>
  monitor_start [port]
  monitor_stop
  state
  mask <left|right|middle|side1|side2|x|y|wheel> <on|off>
  mask_key <key>
  unmask_key <key>
  unmask_all
  trace <on|off>
  debug <port> <on|off>
  lcd_color <rgb565_int>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--uuid", required=True)
    parser.add_argument("--timeout", type=float, default=2.0)
    parser.add_argument("--screen-width", type=int, default=2560)
    parser.add_argument("--screen-height", type=int, default=1440)
    parser.add_argument("--absolute-mode", choices=["corner_random", "top_left_only"], default="corner_random")
    return parser.parse_args()


def resolve_key(token: str) -> int:
    normalized = token.strip()
    if normalized.startswith("0x"):
        return int(normalized, 16)
    upper = normalized.upper()
    if upper in HidKey.__members__:
        return int(HidKey[upper])
    if len(normalized) == 1 and normalized in CHAR_TO_KEY:
        return int(CHAR_TO_KEY[normalized][0])
    raise ValueError(f"Unknown key '{token}'")


def resolve_button(token: str) -> MouseButton:
    return MouseButton[token.strip().upper()]


def resolve_on_off(token: str) -> bool:
    lowered = token.strip().lower()
    if lowered in {"on", "1", "true", "yes"}:
        return True
    if lowered in {"off", "0", "false", "no"}:
        return False
    raise ValueError(f"Expected on/off, got '{token}'")


def print_monitor_state(client: KMBoxClient) -> None:
    monitor = client.monitor
    if monitor is None:
        print("monitor is not running")
        return
    state = monitor.state
    print(
        {
            "mouse_buttons": state.mouse.buttons,
            "mouse_x": state.mouse.x,
            "mouse_y": state.mouse.y,
            "mouse_wheel": state.mouse.wheel,
            "keyboard_modifiers": state.keyboard.modifiers,
            "keyboard_buttons": state.keyboard.buttons,
            "last_event_ts": state.last_event_ts,
        }
    )


def main() -> int:
    args = parse_args()
    client = KMBoxClient(
        args.host,
        args.port,
        args.uuid,
        timeout=args.timeout,
        absolute_mouse=AbsoluteMouseConfig(
            mode=args.absolute_mode,
            screen_width=args.screen_width,
            screen_height=args.screen_height,
        ),
    )

    mask_methods: dict[str, Callable[[bool], bool]] = {
        "left": client.mask_left,
        "right": client.mask_right,
        "middle": client.mask_middle,
        "side1": client.mask_side1,
        "side2": client.mask_side2,
        "x": client.mask_x,
        "y": client.mask_y,
        "wheel": client.mask_wheel,
    }

    print("connected")
    print(HELP_TEXT)

    try:
        while True:
            try:
                raw = input("kmbox> ").strip()
            except EOFError:
                print()
                break
            if not raw:
                continue
            try:
                parts = shlex.split(raw)
            except ValueError as exc:
                print(f"parse error: {exc}")
                continue

            cmd = parts[0].lower()
            args_ = parts[1:]

            try:
                if cmd in {"quit", "exit"}:
                    break
                if cmd == "help":
                    print(HELP_TEXT)
                elif cmd == "press":
                    client.key_press(resolve_key(args_[0]), int(args_[1]) if len(args_) > 1 else 50)
                    print("ok")
                elif cmd == "press_enc":
                    client.key_press(resolve_key(args_[0]), int(args_[1]) if len(args_) > 1 else 50, encrypted=True)
                    print("ok")
                elif cmd == "down":
                    client.key_down(resolve_key(args_[0]))
                    print("ok")
                elif cmd == "up":
                    client.key_up(resolve_key(args_[0]))
                    print("ok")
                elif cmd == "combo":
                    keys = [resolve_key(part) for part in args_[0].split(",") if part.strip()]
                    client.combo(keys, int(args_[1]) if len(args_) > 1 else 50)
                    print("ok")
                elif cmd == "type":
                    client.type_text(" ".join(args_))
                    print("ok")
                elif cmd == "move":
                    client.move(int(args_[0]), int(args_[1]))
                    print("ok")
                elif cmd == "move_enc":
                    client.enc_move(int(args_[0]), int(args_[1]))
                    print("ok")
                elif cmd == "move_auto":
                    client.move_auto(int(args_[0]), int(args_[1]), int(args_[2]))
                    print("ok")
                elif cmd == "bezier":
                    client.move_bezier(*(int(value) for value in args_[:7]))
                    print("ok")
                elif cmd == "click":
                    button = resolve_button(args_[0]) if args_ else MouseButton.LEFT
                    duration = int(args_[1]) if len(args_) > 1 else 50
                    client.click(button, duration)
                    print("ok")
                elif cmd == "click_at":
                    x = int(args_[0])
                    y = int(args_[1])
                    button = resolve_button(args_[2]) if len(args_) > 2 else MouseButton.LEFT
                    duration = int(args_[3]) if len(args_) > 3 else 50
                    client.click_at(x, y, button, duration)
                    print("ok")
                elif cmd == "wheel":
                    client.wheel(int(args_[0]))
                    print("ok")
                elif cmd == "monitor_start":
                    client.monitor_start(int(args_[0]) if args_ else 5002)
                    print("ok")
                elif cmd == "monitor_stop":
                    client.monitor_stop()
                    print("ok")
                elif cmd == "state":
                    print_monitor_state(client)
                elif cmd == "mask":
                    mask_methods[args_[0].lower()](resolve_on_off(args_[1]))
                    print("ok")
                elif cmd == "mask_key":
                    client.mask_keyboard(resolve_key(args_[0]))
                    print("ok")
                elif cmd == "unmask_key":
                    client.unmask_keyboard(resolve_key(args_[0]))
                    print("ok")
                elif cmd == "unmask_all":
                    client.unmask_all()
                    print("ok")
                elif cmd == "trace":
                    client.trace_enable(resolve_on_off(args_[0]))
                    print("ok")
                elif cmd == "debug":
                    client.debug(int(args_[0]), resolve_on_off(args_[1]))
                    print("ok")
                elif cmd == "lcd_color":
                    client.lcd_color(int(args_[0], 0))
                    print("ok")
                else:
                    print(f"unknown command: {cmd}")
            except IndexError:
                print("missing arguments")
            except Exception as exc:
                print(f"error: {exc}")
    finally:
        try:
            client.close()
        except Exception:
            pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
