# OKX 交易员监控

监控 OKX 跟单交易员的持仓变化，实时推送通知到 Telegram。

## 功能

- 监控多个交易员的持仓变化
- 检测开仓、平仓、加仓、减仓操作
- Telegram 实时通知
- 支持通过 OKX 链接或短链接添加交易员
- 热门交易员浏览和添加
- 交易员备注/别名

## 截图

![主界面](docs/screenshot.png)

## 安装

### 方式一：下载可执行文件

从 [Releases](../../releases) 页面下载对应系统的版本：

- **macOS**: `OKX交易员监控.app`
- **Windows**: `OKX交易员监控.exe`

### 方式二：从源码运行

```bash
# 克隆仓库
git clone https://github.com/YOUR_USERNAME/okx-monitor.git
cd okx-monitor

# 安装依赖
pip install -r requirements.txt

# 运行
python main.py
```

## 配置

### OKX API

1. 登录 OKX 网页版
2. 进入「个人中心」→「API」
3. 创建 API Key（只需要**读取**权限）
4. 在软件设置中填入 API Key、Secret Key、Passphrase

### Telegram Bot

1. 在 Telegram 搜索 `@BotFather`
2. 发送 `/newbot` 创建机器人
3. 获取 Bot Token
4. 搜索 `@userinfobot` 获取你的 Chat ID
5. 在软件设置中填入 Bot Token 和 Chat ID

## 使用

1. 打开软件，点击「设置」配置 OKX API 和 Telegram
2. 在「交易员管理」页面添加要监控的交易员
3. 点击「开始监控」
4. 当交易员有操作时，会收到 Telegram 通知

## 添加交易员

支持以下格式：
- OKX 主页链接：`https://www.okx.com/cn/copy-trading/account/xxx`
- 短链接：`https://oyidl.net/ul/xxx`
- uniqueCode：直接输入交易员代码

## 开发

```bash
# 安装开发依赖
pip install -r requirements.txt
pip install pyinstaller

# 打包 macOS
pyinstaller okx-monitor.spec

# 打包 Windows (需要在 Windows 上运行)
pyinstaller okx-monitor-win.spec
```

## License

MIT License
