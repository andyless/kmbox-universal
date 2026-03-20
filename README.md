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
- "absolute-ish" cursor movement by homing to top-left first

## Install

```bash
pip install kmbox-universal
```

## Quick Start

```python
from kmbox_universal import KMBoxClient, HidKey

client = KMBoxClient("192.168.2.188", 6314, "39EBDC32")
client.key_press(HidKey.C, 60)
client.move(100, 0)
client.click("left")
```

## Absolute Click Helper

KMBox Net exposes relative mouse movement, not true absolute cursor positioning.
This package provides a pragmatic helper:

```python
client.click_at(10, 10)
```

It first "homes" to the top-left edge, then moves to the requested target.
This works best when:
- the target machine uses one monitor
- the resolution stays fixed
- pointer acceleration is disabled

## Feature Coverage

- connect
- mouse move / move_auto / bezier / wheel / combined mouse packet
- left/right/middle/side buttons
- keyboard down/up/press/combo/text typing
- encrypted `enc_*` mouse and keyboard commands
- monitor mode
- mouse and keyboard mask/unmask
- set config, set VID/PID, reboot, debug, trace
- LCD solid fill and raw image upload

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
