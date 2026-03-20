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

## 快速开始

```python
from kmbox_universal import KMBoxClient, HidKey

client = KMBoxClient("192.168.2.188", 6314, "39EBDC32")
client.key_press(HidKey.C, 60)
client.move(100, 0)
client.click("left")
```

## 绝对点击辅助

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

## 功能覆盖

- connect
- 鼠标移动 / `move_auto` / Bezier / 滚轮 / `mouse_all`
- 左右中键和侧键
- 键盘按下 / 松开 / 短按 / 组合键 / 文本输入
- `enc_*` 加密键盘鼠标命令
- monitor 模式
- 鼠标和键盘 mask / unmask
- 设置 IP / 端口 / VID / PID
- reboot / debug / trace
- LCD 纯色填充和原始图片上传

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
