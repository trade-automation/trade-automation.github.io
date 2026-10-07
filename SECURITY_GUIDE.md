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

*生成时间：2026-10-07 | 更新于 2026-10-07 | 适用于 Cloudflare Free Plan + GitHub Pages 架构*

---

## 🔒 GEO 与安全的兼容策略

安全性与 GEO 本质互补：安全做得好，站点可信度更高，AI 更愿意引用；GEO 做得好，内容结构化、路径清晰，也便于安全审计和访问控制。冲突只发生在粗放的安全配置上。

### ✅ 不冲突的安全措施（放心做）

| 措施 | 为什么不影响 GEO |
|------|-----------------|
| 隐藏源站 IP / CDN 回源 / HTTPS / HSTS | AI 爬虫访问 CDN 边缘节点，不关心源站 IP |
| WAF 托管规则（SQL 注入/XSS 防护） | 正常 GET 请求不会被拦截 |
| Schema 结构化数据、FAQ、产品参数 | 纯公开内容标记，不涉及敏感数据 |
| 2FA、Tokenization、密码哈希、备份 | 与前端公开内容抓取完全无关 |
| 安全响应头（X-Frame-Options 等） | 只要不阻止 HTML 和 JSON-LD 输出即可 |

### ⚠️ 需要注意冲突的措施

| 措施 | 冲突原因 | 协调方法 |
|------|---------|---------|
| Bot Fight Mode / JS 挑战 / CAPTCHA | AI 爬虫通常不执行 JS，被挑战就抓不到内容 | 对已验证 AI Bot 放行，只挑战未知 Bot |
| 一键屏蔽 AI 爬虫 | 直接切断 GEO 来源 | 不要全站屏蔽，按 UA/IP/路径精细控制 |
| robots.txt 全站 Disallow | 合法 AI 也进不来 | 允许 GPTBot/PerplexityBot 等，仅禁止敏感路径 |
| WAF 自定义 UA 拦截 | 可能误杀 PerplexityBot、Bytespider | 用官方 IP 段 + 反向 DNS 验证，加入白名单 |
| 速率限制 / CC 防护过严 | AI 爬虫多 IP 高频抓取，触发限流 | 对已验证 AI Bot 放宽阈值 |
| 内容依赖 JS 渲染 | AI 不执行 JS，可能读不到 | 用静态 HTML，JSON-LD 直接内联 |
| CSP 阻止内联脚本 | 可能影响 JSON-LD 或页面渲染 | 允许 application/ld+json，或使用 nonce |

### 🎯 兼容原则：精细化，不一刀切

1. **白名单放行合法 AI 爬虫** — 在 Cloudflare 中把 GPTBot、OAI-SearchBot、PerplexityBot、ClaudeBot、Bytespider 加入允许列表，不开"屏蔽所有 AI 爬虫"全局开关
2. **路径隔离** — 公开内容（产品页、博客、FAQ）允许抓取；敏感路径（/social-drafts/ 等内部草稿）在 robots.txt 中禁止
3. **静态化 + 结构化** — 核心内容用静态 HTML，JSON-LD 直接写在 HTML 里，既利于 GEO 也减少攻击面
4. **日志监控区分敌友** — 通过 UA、IP 段、频率区分合法 AI 爬虫和恶意爬虫，定期审计
5. **黑帽 GEO 不碰** — 伪造内容、刷评、投毒会被 AI 引擎降权，得不偿失
