# kmbox-universal

Cross-platform Python client for `KMBox Net` devices.

[中文文档](README.zh-CN.md)

This package merges the useful parts of the public KMBox ecosystem:
- the official `kvmaibox/kmboxnet` protocol and command set
- the Java ergonomics from `OceanTw/KMNet.java`
- the higher-level helpers from `uve192/KMBox.NET`

It adds:
- pure Python UDP transport
- optional encrypted packet sending for `enc_*` operations
- monitor mode with keyboard/mouse state tracking
- mask/unmask helpers
- LCD, debug, VID/PID, reboot, and trace commands
- text typing helpers
- "absolute-ish" cursor movement by homing to a screen corner first

## Install

```bash
pip install kmbox-universal
```

## Public API

Main exports:

- `KMBoxClient`
- `HidKey`
- `MouseButton`
- `KeyboardModifier`
- `AbsoluteMouseConfig`
- `KMBoxError`
- `KMBoxTimeoutError`
- `KMBoxProtocolError`

## Quick Start

```python
from kmbox_universal import KMBoxClient, HidKey, MouseButton

client = KMBoxClient("192.168.2.188", 6314, "39EBDC32")
client.key_press(HidKey.C, 60)
client.move(100, 0)
client.click(MouseButton.LEFT)
client.close()
```

## Interactive Test CLI

After install:

```bash
kmbox-interactive --host 192.168.2.188 --port 6314 --uuid 39EBDC32
```

Or from source:

```bash
PYTHONPATH=src python -m kmbox_universal.interactive --host 192.168.2.188 --port 6314 --uuid 39EBDC32
```

The CLI supports common manual test commands:

- `press c 60`
- `combo LEFT_CTRL,C 60`
- `type hello`
- `move 100 0`
- `move_auto 300 100 200`
- `click left 50`
- `click_at 10 10 left 50`
- `monitor_start 5002`
- `state`
- `mask left on`
- `unmask_all`
- `lcd_color 0xF800`

Use `help` inside the CLI to see the full command list.

## Constructor

```python
KMBoxClient(
    host: str,
    port: int,
    uuid: str,
    *,
    timeout: float = 2.0,
    auto_connect: bool = True,
    absolute_mouse: AbsoluteMouseConfig | None = None,
)
```

Parameters:

- `host`: KMBox device IP
- `port`: KMBox UDP port
- `uuid`: 8 hex characters, for example `39EBDC32`
- `timeout`: socket timeout in seconds
- `auto_connect`: automatically sends the initial connect command
- `absolute_mouse`: settings used by `move_to()` / `click_at()`
  - `mode`: `corner_random` or `top_left_only`
  - `screen_width` / `screen_height`: used when homing from non-top-left corners

## API Coverage

### Connection

- `connect()`
- `close()`

### Mouse

- `move(dx, dy)`
- `enc_move(dx, dy)`
- `move_auto(dx, dy, duration_ms)`
- `enc_move_auto(dx, dy, duration_ms)`
- `move_bezier(dx, dy, duration_ms, x1, y1, x2, y2)`
- `enc_move_bezier(dx, dy, duration_ms, x1, y1, x2, y2)`
- `button(button, is_down)`
- `enc_button(button, is_down)`
- `left(is_down)`
- `right(is_down)`
- `middle(is_down)`
- `side1(is_down)`
- `side2(is_down)`
- `enc_left(is_down)`
- `enc_right(is_down)`
- `enc_middle(is_down)`
- `enc_side1(is_down)`
- `enc_side2(is_down)`
- `click(button=MouseButton.LEFT, duration_ms=50)`
- `wheel(amount)`
- `enc_wheel(amount)`
- `mouse_all(buttons, dx, dy, wheel)`
- `home_top_left()`
- `move_to(x, y, duration_ms=None)`
- `click_at(x, y, button=MouseButton.LEFT, duration_ms=50)`

### Keyboard

- `key_down(key)`
- `enc_key_down(key)`
- `key_up(key)`
- `enc_key_up(key)`
- `key_press(key, duration_ms=50, encrypted=False)`
- `combo(keys, duration_ms=50, encrypted=False)`
- `type_text(text, delay_ms=80)`

### Monitor

- `monitor_start(port=5002, timeout=0.003)`
- `monitor_stop()`
- `isdown_left()`
- `isdown_right()`
- `isdown_middle()`
- `isdown_side1()`
- `isdown_side2()`
- `isdown_keyboard(key)`
- `client.monitor`

`client.monitor` is a `MonitorListener` instance after `monitor_start()`. It can be used for lower-level state reads and callbacks.

### Mask / Unmask

- `mask_left(enabled)`
- `mask_right(enabled)`
- `mask_middle(enabled)`
- `mask_side1(enabled)`
- `mask_side2(enabled)`
- `mask_x(enabled)`
- `mask_y(enabled)`
- `mask_wheel(enabled)`
- `mask_keyboard(key)`
- `unmask_keyboard(key)`
- `unmask_all()`

### Device / Network

- `set_config(ip, port)`
- `set_vid_pid(vid, pid)`
- `reboot()`
- `debug(port, enabled)`
- `trace_enable(enabled)`

### LCD

- `lcd_color(rgb565)`
- `lcd_picture_bottom(image_data)`
- `lcd_picture(image_data)`

Image buffer requirements:

- `lcd_picture_bottom`: exactly `128 * 80 * 2` bytes
- `lcd_picture`: exactly `128 * 160 * 2` bytes
- format: raw RGB565

## Common Examples

### Press a Key

```python
from kmbox_universal import KMBoxClient, HidKey

client = KMBoxClient("192.168.2.188", 6314, "39EBDC32")
client.key_press(HidKey.F1, 80)
client.close()
```

### Combo

```python
from kmbox_universal import KMBoxClient, HidKey

client = KMBoxClient("192.168.2.188", 6314, "39EBDC32")
client.combo([HidKey.LEFT_CTRL, HidKey.C], duration_ms=60)
client.close()
```

### Type Text

```python
from kmbox_universal import KMBoxClient

client = KMBoxClient("192.168.2.188", 6314, "39EBDC32")
client.type_text("Hello 123", delay_ms=70)
client.close()
```

### Relative Mouse Move

```python
from kmbox_universal import KMBoxClient

client = KMBoxClient("192.168.2.188", 6314, "39EBDC32")
client.move(200, 0)
client.wheel(10)
client.close()
```

### Interpolated Mouse Move

```python
from kmbox_universal import KMBoxClient

client = KMBoxClient("192.168.2.188", 6314, "39EBDC32")
client.move_auto(300, 120, 250)
client.close()
```

### Bezier Mouse Move

```python
from kmbox_universal import KMBoxClient

client = KMBoxClient("192.168.2.188", 6314, "39EBDC32")
client.move_bezier(300, 100, 220, 80, 0, 220, 100)
client.close()
```

### Encrypted Packets

```python
from kmbox_universal import KMBoxClient, HidKey

client = KMBoxClient("192.168.2.188", 6314, "39EBDC32")
client.enc_move(50, 0)
client.enc_left(True)
client.enc_left(False)
client.key_press(HidKey.C, 50, encrypted=True)
client.close()
```

### Monitor Mode

```python
from kmbox_universal import KMBoxClient, HidKey
import time

client = KMBoxClient("192.168.2.188", 6314, "39EBDC32")
client.monitor_start(5002)

for _ in range(50):
    if client.isdown_left():
        print("left mouse is down")
    if client.isdown_keyboard(HidKey.A):
        print("A is down")
    time.sleep(0.05)

client.monitor_stop()
client.close()
```

### Mask / Unmask

```python
from kmbox_universal import KMBoxClient, HidKey

client = KMBoxClient("192.168.2.188", 6314, "39EBDC32")
client.mask_left(True)
client.mask_x(True)
client.mask_keyboard(HidKey.A)

# do work...

client.unmask_all()
client.close()
```

### Absolute Click Helper

KMBox Net exposes relative mouse movement, not true absolute cursor positioning.
This package provides a pragmatic helper:

```python
client.click_at(10, 10)
```

By default it first homes to one of the four screen corners at random, then moves from that corner to the requested target.
If you want the old fixed behavior, use `AbsoluteMouseConfig(mode="top_left_only")`.

Example:

```python
from kmbox_universal import AbsoluteMouseConfig, KMBoxClient

client = KMBoxClient(
    "192.168.2.188",
    6314,
    "39EBDC32",
    absolute_mouse=AbsoluteMouseConfig(
        mode="corner_random",
        screen_width=2560,
        screen_height=1440,
    ),
)
client.click_at(10, 10)
client.close()
```

This works best when:
- the target machine uses one monitor
- the resolution stays fixed
- pointer acceleration is disabled

### LCD

```python
from kmbox_universal import KMBoxClient

client = KMBoxClient("192.168.2.188", 6314, "39EBDC32")
client.lcd_color(0xF800)  # red
client.close()
```

## Notes

- The package speaks UDP directly to the device.
- `uuid` must be 8 hex characters.
- `enc_*` support is implemented from the public protocol behavior.
- `move_to()` / `click_at()` are practical helpers, not true hardware absolute positioning.
- Side buttons are supported at the protocol level, but physical behavior depends on device firmware.

## Errors

Main exceptions:

- `KMBoxError`: base error
- `KMBoxTimeoutError`: device did not reply before timeout
- `KMBoxProtocolError`: response header did not match the request

## References

These repositories were used as public references while building this package:
- https://github.com/kvmaibox/kmboxnet
- https://github.com/OceanTw/KMNet.java
- https://github.com/uve192/KMBox.NET

## Publish

Build:

```bash
python -m build
```

Test:

```bash
pytest
```
