# 旧手机部署指南 (Android)

## 准备
- 一部 Android 旧手机（Android 7+）
- 保持手机充电和WiFi连接

## 步骤

### 1. 安装 Termux
从 F-Droid 下载安装（不要从 Play Store）：
https://f-droid.org/packages/com.termux/

### 2. 打开 Termux，安装 Python
```bash
pkg update && pkg upgrade -y
pkg install python git -y
pip install requests python-telegram-bot
```

### 3. 下载监控脚本
```bash
git clone https://github.com/gaobi639-netizen/okx-monitor.git
cd okx-monitor
```

### 4. 运行监控
```bash
python server_monitor.py
```

### 5. 后台运行（关闭Termux也能继续）
```bash
# 安装 tmux
pkg install tmux -y

# 创建后台会话
tmux new -s monitor

# 在 tmux 里运行
python server_monitor.py

# 按 Ctrl+B 然后按 D 退出（脚本继续运行）
# 重新进入查看: tmux attach -t monitor
```

### 6. 防止手机休眠
1. 设置 → 电池 → 关闭 Termux 的电池优化
2. Termux 里运行: `termux-wake-lock`

## 添加/修改交易员

编辑 `server_monitor.py` 文件中的 CONFIG：

```python
"traders": {
    "交易员uniqueCode": "备注名称",
    "90BCC01689ED93F0": "炒币猛",
    "C7966D1C938416B0": "梭哈以太"
}
```

## 常用命令

```bash
# 查看运行中的监控
tmux attach -t monitor

# 停止监控
Ctrl + C

# 重启监控
python server_monitor.py
```
