# iKuuu 每日签到

此仓库的 `main2.yml` 通过登录 Cookie 调用 iKuuu 签到接口。自动任务不会模拟邮箱密码登录，也不会发送邮件。

## 为什么改用 Cookie

iKuuu 的邮箱密码 API 登录目前会返回登录流程校验错误。开源项目 [auto_checkin](https://github.com/tangtao-xp1/auto_checkin) 已改为浏览器 Cookie 认证：从官网登录态获取 Cookie，再直接请求 `/user/checkin`。Cookie 过期、域名不匹配或签到接口未确认成功时，工作流会明确失败，不会误报成功。

## 配置

在仓库的 **Settings → Secrets and variables → Actions → New repository secret** 中设置：

| Secret | 内容 |
| --- | --- |
| `IKUUU_COOKIE` | 官网登录 Cookie；多个账号用 `||` 分隔 |
| `IKUUU_BASE_URL` | 获取该 Cookie 时登录的官网地址，例如 `https://ikuuu.top` |
| `SCKEY` | 可选，Server 酱推送密钥 |
| `TOKEN` | 可选，PushPlus 推送密钥 |

获取 Cookie 时，在浏览器登录**与 `IKUUU_BASE_URL` 相同的域名**。可在浏览器开发者工具的 Application/Storage → Cookies 中复制该站点的登录 Cookie，并按 `名称=值; 名称=值` 拼接。请勿把 Cookie 发到聊天、截图或公开日志中；它相当于登录凭据。Life System 的签到设置会把 Cookie 直接写入 GitHub Actions Secrets，不在本机保存。

`IKUUU_BASE_URL` 必须与 Cookie 所属域名一致。账号和 Cookie 同时有多个时，按顺序使用 `||` 分隔。

## 工作流

- `main2.yml` 使用 GitHub Actions Secrets，每天北京时间 06:00 自动运行，也可以从 Actions 页面手动运行。
- 登录 Cookie 直接用于签到请求，不调用密码登录接口，也不触发登录验证码邮件。
- 只有接口明确返回签到成功或今日已签到时才算成功；Cookie 失效、地址不匹配、接口错误都会以失败结束。
- 不配置 `SCKEY` 或 `TOKEN` 时不会发送签到推送；仓库脚本不含邮件发送功能。
