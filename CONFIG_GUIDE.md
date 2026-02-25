# OKX 跟单监控系统 - 详细配置教程

## 目录
1. [OKX API 配置](#1-okx-api-配置)
2. [Telegram Bot 配置](#2-telegram-bot-配置)
3. [应用程序配置](#3-应用程序配置)
4. [常见问题](#4-常见问题)

---

## 1. OKX API 配置

### 1.1 登录 OKX

1. 打开浏览器，访问 [https://www.okx.com](https://www.okx.com)
2. 点击右上角「登录」
3. 输入账号密码，完成二次验证

### 1.2 进入 API 管理页面

1. 登录后，点击右上角头像
2. 在下拉菜单中选择「API」
3. 或直接访问：[https://www.okx.com/account/my-api](https://www.okx.com/account/my-api)

### 1.3 创建 API Key

1. 点击「创建 API」或「Create API」按钮

2. **填写基本信息：**
   ```
   API 名称：OKX-Monitor（自定义名称）
   密码短语：设置一个密码（重要！需要记住，后面要用）
   ```

3. **设置权限（重要）：**
   ```
   ✅ 读取 (Read)          ← 必须勾选
   ❌ 交易 (Trade)         ← 不要勾选
   ❌ 提币 (Withdraw)      ← 不要勾选
   ```
   > ⚠️ 安全提示：只勾选「读取」权限，不要开启交易和提币权限

4. **IP 限制（可选）：**
   - 如果你有固定 IP，建议填写以增强安全性
   - 如果 IP 经常变化，可以留空

5. 点击「确认」，完成手机/邮箱验证

### 1.4 保存 API 信息

创建成功后，你会看到以下信息（**只显示一次，务必保存**）：

```
┌─────────────────────────────────────────────────────────────┐
│  API Key:        xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx       │
│  Secret Key:     XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX           │
│  Passphrase:     你设置的密码短语                             │
└─────────────────────────────────────────────────────────────┘
```

> ⚠️ **重要**：Secret Key 只显示一次，请立即复制保存到安全的地方！

### 1.5 在应用中填写

打开 OKX Monitor 应用，在「配置」标签页填入：

| 字段 | 说明 | 示例 |
|------|------|------|
| API Key | API 密钥 | `a1b2c3d4-e5f6-7890-abcd-ef1234567890` |
| Secret Key | 密钥 | `ABCDEFGHIJKLMNOPQRSTUVWXYZ123456` |
| Passphrase | 密码短语 | `你设置的密码` |

---

## 2. Telegram Bot 配置

### 2.1 创建 Telegram Bot

1. 打开 Telegram，搜索 `@BotFather`（官方机器人）

2. 点击进入对话，发送：
   ```
   /newbot
   ```

3. BotFather 会问你机器人的名称，输入一个名字：
   ```
   OKX 跟单提醒
   ```

4. 接着输入机器人的用户名（必须以 `bot` 结尾）：
   ```
   my_okx_monitor_bot
   ```

5. 创建成功后，BotFather 会返回 **Bot Token**：
   ```
   Done! Congratulations on your new bot.

   Use this token to access the HTTP API:
   7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

6. **保存这个 Token**，格式类似：
   ```
   7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

### 2.2 获取你的 Chat ID

**方法一：使用 @userinfobot**

1. 在 Telegram 搜索 `@userinfobot`
2. 点击「Start」或发送任意消息
3. 机器人会回复你的信息，包含 `Id` 字段：
   ```
   Id: 123456789
   First: 你的名字
   Lang: zh-hans
   ```
4. 这个 `123456789` 就是你的 Chat ID

**方法二：使用 @getmyid_bot**

1. 搜索 `@getmyid_bot`
2. 发送 `/start`
3. 获取返回的 ID

**方法三：使用 @RawDataBot**

1. 搜索 `@RawDataBot`
2. 发送任意消息
3. 在返回的 JSON 中找到 `"id"` 字段

### 2.3 激活你的 Bot

> ⚠️ **重要步骤**：必须先和 Bot 对话，Bot 才能给你发消息

1. 在 Telegram 搜索你刚创建的 Bot 用户名（如 `@my_okx_monitor_bot`）
2. 点击「Start」或发送 `/start`
3. 这样 Bot 就可以给你发送消息了

### 2.4 在应用中填写

在 OKX Monitor 应用的「配置」标签页填入：

| 字段 | 说明 | 示例 |
|------|------|------|
| Bot Token | 机器人令牌 | `7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |
| Chat ID | 你的用户 ID | `123456789` |

### 2.5 测试连接

1. 点击「测试连接」按钮
2. 如果配置正确，你会在 Telegram 收到测试消息：
   ```
   🔔 OKX Monitor 测试消息

   连接成功！
   ```

---

## 3. 应用程序配置

### 3.1 监控设置

| 设置 | 说明 | 建议值 |
|------|------|--------|
| 轮询间隔 | 检查持仓变化的频率 | 10 秒 |

> 💡 轮询间隔说明：
> - 5 秒：更及时，但 API 调用更频繁
> - 10 秒：平衡选择（推荐）
> - 30 秒：更省资源，但延迟较高

### 3.2 添加监控交易员

1. 确保你在 OKX 网页/App 上已经「关注」了一些交易员
2. 在应用中切换到「交易员」标签
3. 点击「刷新列表」获取你关注的交易员
4. 选择要监控的交易员，点击「添加监控」
5. 可以添加多个交易员

### 3.3 开始监控

1. 确保至少添加了一个交易员
2. 点击右上角「开始监控」按钮
3. 状态变为绿色「运行中」表示监控已启动
4. 日志面板会显示监控状态

---

## 4. 常见问题

### Q1: OKX API 连接失败？

**可能原因：**
- API Key 或 Secret Key 复制错误
- Passphrase 输入错误
- API 权限不足（需要「读取」权限）
- IP 限制不匹配

**解决方法：**
1. 重新复制 API 信息，注意不要有空格
2. 检查 Passphrase 是否正确
3. 在 OKX 网页检查 API 权限设置

### Q2: Telegram 收不到消息？

**可能原因：**
- 没有先和 Bot 对话
- Bot Token 错误
- Chat ID 错误

**解决方法：**
1. 确保已经给 Bot 发送过 `/start`
2. 重新检查 Token 和 Chat ID
3. 使用「测试连接」功能验证

### Q3: 刷新交易员列表为空？

**可能原因：**
- 你在 OKX 上没有关注任何交易员
- API 权限问题

**解决方法：**
1. 先在 OKX App/网页上关注一些交易员
2. 然后再刷新列表

### Q4: 监控没有检测到交易？

**说明：**
- 监控启动后首次获取持仓作为基准
- 只有持仓发生变化才会触发通知
- 交易员需要有新的开仓/平仓操作

### Q5: 如何获取群组的 Chat ID？

如果想把通知发到群组：

1. 把 Bot 添加到群组
2. 在群组中发送任意消息
3. 访问：`https://api.telegram.org/bot<YourToken>/getUpdates`
4. 在返回的 JSON 中找到群组的 `chat.id`（负数）

---

## 快速检查清单

```
□ OKX API Key 已创建
□ OKX API 已开启「读取」权限
□ Secret Key 和 Passphrase 已保存
□ Telegram Bot 已创建
□ 已获取 Bot Token
□ 已获取个人 Chat ID
□ 已和 Bot 发送过 /start
□ 应用配置已保存
□ 已添加监控交易员
□ 测试连接全部通过
```

---

## 联系支持

如有问题，请检查：
1. 日志面板的错误信息
2. 确认网络连接正常
3. 确认 API 密钥有效

祝你使用愉快！🎉
