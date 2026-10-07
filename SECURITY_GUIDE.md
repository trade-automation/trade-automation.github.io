# foshanFFE.com Cloudflare 安全加固配置指南

> 当前状态：✅ Cloudflare 代理已启用 | ✅ HSTS 已开启 | ⚠️ 以下配置需在 Cloudflare Dashboard 手动完成

---

## 🔴 优先级 P0 — 立即配置

### 1. WAF 托管规则集（Managed Rules）

**路径：** Security → WAF → Managed rules

| 设置项 | 推荐值 |
|--------|--------|
| OWASP ModSecurity Core Rule Set | 启用，Medium sensitivity |
| Cloudflare Managed Ruleset | 启用 |
| Exposed Credentials Check | 启用 |

**说明：** 自动拦截 SQL 注入、XSS、远程代码执行等常见攻击，规则每周更新。

---

### 2. 安全响应头（通过 Transform Rules 添加）

**路径：** Rules → Transform Rules → Modify Response Header

创建一条规则，条件设为 `Hostname = foshanffe.com`，添加以下响应头：

| Header | Value | 说明 |
|--------|-------|------|
| `X-Frame-Options` | `DENY` | 防止点击劫持 |
| `X-Content-Type-Options` | `nosniff` | 阻止 MIME 嗅探 |
| `X-XSS-Protection` | `1; mode=block` | IE/旧浏览器 XSS 过滤 |
| `Permissions-Policy` | `accelerometer=(), camera=(), microphone=(), geolocation=()` | 限制浏览器功能调用 |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | 控制 Referrer 信息泄露 |

**注意：** 如果 HTML 已有同名 meta 标签，HTTP 响应头优先级更高，以响应头为准。

---

### 3. SSL/TLS 加密模式确认

**路径：** SSL/TLS → Overview

| 设置项 | 推荐值 |
|--------|--------|
| Encryption mode | **Full (Strict)** |
| Always Use HTTPS | **开启** |
| Automatic HTTPS Rewrites | **开启** |
| Minimum TLS Version | **TLS 1.2** |

---

## 🟡 优先级 P1 — 一周内配置

### 4. Bot 防护

**路径：** Security → Bots

| 设置项 | 推荐值 |
|--------|--------|
| Bot Fight Mode | **启用**（免费计划可用） |
| Super Bot Fight Mode | 如有 Pro 计划则启用 |

---

### 5. Rate Limiting（速率限制）

**路径：** Security → WAF → Rate limiting rules

创建规则：

| 条件 | 值 |
|------|-----|
| 匹配条件 | `Hostname = foshanffe.com` |
| 平均请求数 | 100 次 / 10 秒（按 IP） |
| 操作 | Block 30 分钟 |

**说明：** 防止 CC 攻击和暴力爬取。静态页面站点可适当放宽。

---

### 6. 隐藏源站 IP

**路径：** DNS → Records

检查事项：
- ✅ 所有 A/CNAME 记录的代理状态（橙色云朵 ☁️）必须为 **Proxied**
- ❌ 不允许任何直接指向源站 IP 的 A 记录
- ❌ 删除不必要的子域名记录（test、dev、admin 等）

**验证方法：**
```bash
# 检查 DNS 记录是否都走代理
dig foshanffe.com +short
# 应该返回 Cloudflare IP，而非真实源站 IP
```

---

### 7. 回源校验（可选，增强）

如果未来有独立服务器（非 GitHub Pages），在 Cloudflare 配置：

**路径：** Rules → Transform Rules → Modify Request Header

添加自定义请求头：
- Header: `X-Source-Verify`
- Value: 随机字符串（如 `ffe-2026-secure`）

源站 Nginx 配置校验该请求头，拒绝无此头的直连请求。

> ⚠️ 当前站点托管在 GitHub Pages，无法自定义 Nginx 配置，此项暂不适用。

---

## 🟢 优先级 P2 — 持续维护

### 8. 安全事件监控

**路径：** Security → Events

- 开启 Security Events 日志
- 定期查看被拦截的请求模式
- 关注异常高频 IP

### 9. 备份策略

| 项目 | 频率 | 说明 |
|------|------|------|
| GitHub 仓库 | 每次 push 自动备份 | GitHub 自带版本历史 |
| Cloudflare 配置 | 每月导出一次 | 记录 Dashboard 配置截图 |
| 本地代码 | 保持 Git 同步 | 确保本地有完整副本 |

### 10. 定期安全审计

- **每月一次**：检查 Cloudflare Security Events，审查新拦截规则
- **每季度一次**：用 [SecurityHeaders.com](https://securityheaders.com/?q=foshanffe.com) 扫描评分
- **每季度一次**：审查第三方脚本依赖（GA4、Google Fonts 等）的完整性

---

## 📋 配置完成检查清单

配置完成后，用以下命令验证：

```bash
curl -sI https://foshanffe.com | grep -iE "x-frame|x-content|strict-transport|content-security|permissions-policy|referrer-policy|x-xss"
```

预期输出应包含：
```
x-frame-options: DENY
x-content-type-options: nosniff
strict-transport-security: max-age=31556952
referrer-policy: strict-origin-when-cross-origin
permissions-policy: accelerometer=(), camera=(), microphone=(), geolocation=()
```

---

*生成时间：2026-10-07 | 适用于 Cloudflare Free Plan + GitHub Pages 架构*
