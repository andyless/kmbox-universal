# kmbox-universal

`KMBox Net` 的跨平台 Python 客户端。

[English README](README.md)

这个包整合了公开 KMBox 生态里最有价值的部分：
- 官方 `kvmaibox/kmboxnet` 的协议和命令集
- `OceanTw/KMNet.java` 的 API 设计思路
- `uve192/KMBox.NET` 的高层易用性封装

并额外提供：
- 纯 Python UDP 传输
- 可选的 `enc_*` 加密发包
- 键盘鼠标监控模式
- 键盘鼠标 mask / unmask
- LCD、debug、VID/PID、reboot、trace 命令
- 文本输入辅助
- 通过“先归零再移动”实现的近似绝对坐标点击

## 安装

```bash
pip install kmbox-universal
```

## 对外 API

主要导出：

- `KMBoxClient`
- `HidKey`
- `MouseButton`
- `KeyboardModifier`
- `AbsoluteMouseConfig`
- `KMBoxError`
- `KMBoxTimeoutError`
- `KMBoxProtocolError`

## 快速开始

```python
from kmbox_universal import KMBoxClient, HidKey, MouseButton

client = KMBoxClient("192.168.2.188", 6314, "39EBDC32")
client.key_press(HidKey.C, 60)
client.move(100, 0)
client.click(MouseButton.LEFT)
client.close()
```

## 构造函数

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

参数说明：

- `host`：设备 IP
- `port`：设备 UDP 端口
- `uuid`：8 位十六进制字符串，例如 `39EBDC32`
- `timeout`：socket 超时时间，单位秒
- `auto_connect`：初始化时是否自动发送连接命令
- `absolute_mouse`：`move_to()` / `click_at()` 使用的近似绝对定位参数

## 功能清单

### 连接

- `connect()`
- `close()`

### 鼠标

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

### 键盘

- `key_down(key)`
- `enc_key_down(key)`
- `key_up(key)`
- `enc_key_up(key)`
- `key_press(key, duration_ms=50, encrypted=False)`
- `combo(keys, duration_ms=50, encrypted=False)`
- `type_text(text, delay_ms=80)`

### 监控

- `monitor_start(port=5002, timeout=0.003)`
- `monitor_stop()`
- `isdown_left()`
- `isdown_right()`
- `isdown_middle()`
- `isdown_side1()`
- `isdown_side2()`
- `isdown_keyboard(key)`
- `client.monitor`

调用 `monitor_start()` 后，`client.monitor` 会变成一个 `MonitorListener` 实例，可进一步读取状态或挂回调。

### 屏蔽 / 解除屏蔽

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

### 设备 / 网络

- `set_config(ip, port)`
- `set_vid_pid(vid, pid)`
- `reboot()`
- `debug(port, enabled)`
- `trace_enable(enabled)`

### LCD

- `lcd_color(rgb565)`
- `lcd_picture_bottom(image_data)`
- `lcd_picture(image_data)`

图片数据要求：

- `lcd_picture_bottom`：长度必须为 `128 * 80 * 2`
- `lcd_picture`：长度必须为 `128 * 160 * 2`
- 格式：原始 RGB565

## 常见示例

### 按键短按

```python
from kmbox_universal import KMBoxClient, HidKey

client = KMBoxClient("192.168.2.188", 6314, "39EBDC32")
client.key_press(HidKey.F1, 80)
client.close()
```

### 组合键

```python
from kmbox_universal import KMBoxClient, HidKey

client = KMBoxClient("192.168.2.188", 6314, "39EBDC32")
client.combo([HidKey.LEFT_CTRL, HidKey.C], duration_ms=60)
client.close()
```

### 文本输入

```python
from kmbox_universal import KMBoxClient

client = KMBoxClient("192.168.2.188", 6314, "39EBDC32")
client.type_text("Hello 123", delay_ms=70)
client.close()
```

### 相对鼠标移动

```python
from kmbox_universal import KMBoxClient

client = KMBoxClient("192.168.2.188", 6314, "39EBDC32")
client.move(200, 0)
client.wheel(10)
client.close()
```

### 自动插值移动

```python
from kmbox_universal import KMBoxClient

client = KMBoxClient("192.168.2.188", 6314, "39EBDC32")
client.move_auto(300, 120, 250)
client.close()
```

### Bezier 移动

```python
from kmbox_universal import KMBoxClient

client = KMBoxClient("192.168.2.188", 6314, "39EBDC32")
client.move_bezier(300, 100, 220, 80, 0, 220, 100)
client.close()
```

### 加密命令

```python
from kmbox_universal import KMBoxClient, HidKey

client = KMBoxClient("192.168.2.188", 6314, "39EBDC32")
client.enc_move(50, 0)
client.enc_left(True)
client.enc_left(False)
client.key_press(HidKey.C, 50, encrypted=True)
client.close()
```

### 监控模式

```python
from kmbox_universal import KMBoxClient, HidKey
import time

client = KMBoxClient("192.168.2.188", 6314, "39EBDC32")
client.monitor_start(5002)

for _ in range(50):
    if client.isdown_left():
        print("鼠标左键按下")
    if client.isdown_keyboard(HidKey.A):
        print("A 键按下")
    time.sleep(0.05)

client.monitor_stop()
client.close()
```

### 输入屏蔽

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

### 绝对点击辅助

`KMBox Net` 原生提供的是相对鼠标移动，不是真正的绝对坐标定位。

这个包提供了一个实用方案：

```python
client.click_at(10, 10)
```

执行逻辑是：
1. 先把鼠标持续推到左上角边界
2. 把那个位置近似当作 `(0, 0)`
3. 再从左上角相对移动到目标点
4. 执行点击

这个方案在以下条件下效果最好：
- 目标机器只有一个显示器
- 分辨率固定
- 鼠标加速度关闭

### LCD

```python
from kmbox_universal import KMBoxClient

client = KMBoxClient("192.168.2.188", 6314, "39EBDC32")
client.lcd_color(0xF800)  # 红色
client.close()
```

## 使用说明

- 本包直接通过 UDP 和设备通信。
- `uuid` 必须是 8 位十六进制字符串。
- `enc_*` 是基于公开协议行为实现的加密发包。
- `move_to()` / `click_at()` 是工程化近似方案，不是真正的硬件绝对定位。
- 侧键命令协议上支持，但具体效果取决于设备固件。

## 异常

主要异常：

- `KMBoxError`：基础异常
- `KMBoxTimeoutError`：设备超时未响应
- `KMBoxProtocolError`：响应头与请求不匹配

## 参考实现

这个包在实现时参考了以下公开仓库：
- https://github.com/kvmaibox/kmboxnet
- https://github.com/OceanTw/KMNet.java
- https://github.com/uve192/KMBox.NET

## 发布

构建：

```bash
python -m build
```

测试：

```bash
pytest
```
