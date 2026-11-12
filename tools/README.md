# 站点预提交校验（site_check.py）

改完站、提交之前跑一遍。有错误就停下修，别提交。

## 怎么跑

```bash
cd /Coze/Drive/Elias/所有对话/主对话
python3 tools/site_check.py site_work_20261029/site --skip-assets
```

本地镜像只同步了 HTML，图片和文档没同步，所以日常固定加 `--skip-assets`。
等哪天把 `images/` 和 `documents/` 也同步下来，就可以去掉这个开关，连资源存在性一起查。

## 怎么看结果

分三块：

**■ 错误 N 项（阻塞提交）**
结构性错误。提交上去 Google 会报错、用户会点到 404。必须修完才能提交。

**■ 警告 N 项（建议修）**
不影响能不能上线，但影响效果。title 过长会在搜索结果里被截断、description 太短没吸引力、页面太薄排名上不去。可以分批修，不用卡提交。

**■ 批量问题 N 处（同类聚合）**
同一类问题散在很多页面时的汇总。比如「181 个页面缺 favicon 声明」——修的时候是批量修，所以聚合成一条，不刷屏。

## 退出码

- `0` = 通过，可以提交
- `1` = 有错误，禁止提交
- `2` = 参数或目录问题

脚本可以接在别的流程里：`python3 tools/site_check.py ... || echo "别提交"`

## 其他参数

```bash
--strict         # 警告也算失败，用于大改前的完整体检
--only-errors    # 只看错误，快速确认能不能提交
--json out.json  # 输出机器可读结果，方便统计和对比
```

## 检查了什么

### 会阻塞提交（错误）

| 检查 | 说明 |
| --- | --- |
| JSON-LD 解析 | 结构化数据块能不能解析、有没有 `@context` / `@type` |
| Schema 引用 | `image` / `logo` / `url` 指向的站内文件是否真实存在 |
| Product schema | 有没有 `image` 和 `offers.price`（B2B 询价页应该用 Service，不是 Product） |
| FAQPage 结构 | `mainEntity` 是否完整、每条有没有 `name` 和 `acceptedAnswer.text` |
| BreadcrumbList | `item` 指向的页面是否存在 |
| H1 | 必须有且只有 1 个 |
| favicon | 声明了但文件不存在 |
| 图片 | `src` 指向的文件不存在 |
| 内部链接 | 指向不存在的页面 |
| footer 位置 | 是否被写在 `</body>` 之后 |
| sitemap | 列出的 URL 是否存在 |

### 只报警告

| 检查 | 阈值 |
| --- | --- |
| title 长度 | 20–65 字符（超出 SERP 会截断） |
| title 重复 | 多个页面共用同一个 title |
| description 长度 | 70–170 字符 |
| description 重复 | 多个页面共用同一个 description |
| canonical | 缺失，或与文件路径不一致 |
| Open Graph | 缺 `og:title` / `og:description` / `og:image` / `og:url` |
| 图片 alt | 有 `src` 但 `alt` 为空 |
| FAQ 一致性 | schema 条数 ≠ 页面可见 FAQ 条数（Google 要求一致） |
| 内容量 | 正文少于 300 词 |
| 孤儿页 | 没有任何站内页面链向它 |
| sitemap 反向 | 站上有页面但 sitemap 没列 |
| sitemap lastmod | 是未来日期 |

## 已知局限

**资源文件不在本地镜像里。**
`images/`、`documents/` 这些目录没有同步，所以不带 `--skip-assets` 跑会报几百条「图片文件不存在」的假错。这不是站的问题，是本地镜像不完整。

**不检查线上是否生效。**
脚本只看本地文件。提交后还要等 GitHub Pages 构建（当前 15–25 分钟），再用带随机参数的 URL 绕过 Cloudflare 缓存验证：
```bash
curl -s -o /dev/null -w "%{http_code}" "https://foshanffe.com/xxx.html?r=$RANDOM"
```
不带参数可能是 Cloudflare 缓存的旧结果（它会把 404 缓存一年）。

**不做内容质量判断。**
措辞、准确性、英文地道程度不在脚本范围内。那些靠人工和 `ffe-humanizer`。

## 加新检查项

在 `check_page`（页面级）或 `check_site_level`（站点级）里加，用：
- `report.error(file, "检查名", "说明")` → 阻塞提交
- `report.warn(file, "检查名", "说明")` → 建议修
- `report.tally("检查名", file)` → 同类问题聚合，适合批量修的场景

加完跑一遍全站，先确认新检查项报出来的不是误报，再纳入日常。
