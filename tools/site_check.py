#!/usr/bin/env python3
"""
foshanFFE.com 站点预提交校验

用途：每次改站、提交前跑一遍，把"埋了两个月才被 Google 发现"的错误提前抓出来。

用法：
    python3 tools/site_check.py site_work_20261029/site
    python3 tools/site_check.py site_work_20261029/site --strict        # 警告也算失败
    python3 tools/site_check.py site_work_20261029/site --json out.json # 机器可读
    python3 tools/site_check.py site_work_20261029/site --only-errors   # 只看错误

退出码：
    0 = 通过（可提交）
    1 = 有错误（禁止提交）
    2 = 参数或目录问题

检查项来源：2026-11-01 排查出的全部问题类型
  - Product schema 用错类型 / 缺必填字段（9 个页面）
  - schema 引用的图片文件不存在（13 个页面引用 404 的 logo）
  - favicon 缺失（181 个页面）
  - H1 数量异常、title/description 缺失或超长
  - 内部链接指向不存在的页面
  - sitemap 与真实文件不一致
"""

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import unquote, urlparse

# ─────────────────────────────────────────────────────────────
# 阈值（按 Google SERP 实际截断位置定，不是拍脑袋）
# ─────────────────────────────────────────────────────────────
TITLE_MIN, TITLE_MAX = 20, 65
DESC_MIN, DESC_MAX = 70, 170
SITE_HOST = "foshanffe.com"

# 资源型扩展名：出现在 href 里说明是下载/图片，不做页面存在性检查以外的判断
ASSET_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg", ".pdf",
             ".mp4", ".webm", ".zip", ".ico", ".css", ".js", ".xml", ".txt",
             ".dwg", ".dxf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"}

SKIP_SCHEMES = ("http://", "https://", "//", "data:", "mailto:", "tel:",
                "javascript:", "whatsapp:", "ftp:")

# Product schema 的富媒体必填字段（Google 原文要求）
PRODUCT_REQUIRED = ["image", "offers"]


class Report:
    """收集并分级输出结果。"""

    def __init__(self):
        self.errors = []      # 阻塞提交
        self.warnings = []    # 建议修
        self.infos = []
        self.stats = {}
        self.counters = defaultdict(list)   # 同类问题按页面聚合，避免刷屏

    def tally(self, name, path):
        self.counters[name].append(path)

    def error(self, path, check, msg):
        self.errors.append({"file": path, "check": check, "msg": msg})

    def warn(self, path, check, msg):
        self.warnings.append({"file": path, "check": check, "msg": msg})

    def info(self, msg):
        self.infos.append(msg)


# ─────────────────────────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────────────────────────

def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s or "").strip()


def norm_space(s):
    return re.sub(r"\s+", " ", (s or "")).strip()


def to_local_path(site_root, url):
    """把站内 URL 转成本地文件路径；外部 URL 返回 None。"""
    if not url:
        return None
    u = url.strip()
    if u.startswith(("http://", "https://")):
        p = urlparse(u)
        if p.netloc.replace("www.", "") != SITE_HOST:
            return None
        path = p.path
    elif u.startswith("//"):
        return None
    elif u.startswith("/"):
        path = u.split("#")[0].split("?")[0]
    else:
        return None  # 相对路径由调用方按文件位置解析

    path = unquote(path)
    if not path or path == "/":
        return site_root / "index.html"
    return site_root / path.lstrip("/")


def resolve_ref(site_root, html_file, ref):
    """把页面里的引用（相对/绝对/站内 URL）解析成候选本地路径。"""
    if not ref:
        return None
    ref = ref.strip()
    if ref.startswith(SKIP_SCHEMES) or ref.startswith("#"):
        return None
    # Cloudflare Email Obfuscation 注入的假链接
    if ref.startswith("/cdn-cgi/") or "cdn-cgi/l/email-protection" in ref:
        return None
    if ref.startswith("http://") or ref.startswith("https://") or ref.startswith("//"):
        return to_local_path(site_root, ref)
    ref = unquote(ref.split("#")[0].split("?")[0])
    if not ref:
        return None
    if ref.startswith("/"):
        return site_root / ref.lstrip("/")
    return (html_file.parent / ref)


def path_exists(site_root, p):
    """文件存在？目录则看 index.html。"""
    if p is None:
        return True  # 不检查的对象一律放过
    try:
        p = p.resolve()
    except Exception:
        return True
    if p.is_file():
        return True
    if p.is_dir():
        return (p / "index.html").is_file()
    # 省略扩展名的站内链接（如 services/index.html -> href="guestroom-ffe"）
    if p.suffix == "" and p.with_suffix(".html").is_file():
        return True
    return False


def collect_files(site_root, suffix=".html"):
    out = []
    for dirpath, dirnames, filenames in os.walk(site_root):
        # 跳过隐藏目录和常见无关目录
        dirnames[:] = [d for d in dirnames
                       if not d.startswith(".") and d not in {"node_modules", "__pycache__"}]
        for fn in filenames:
            if fn.endswith(suffix):
                out.append(Path(dirpath) / fn)
    return sorted(out)


# ─────────────────────────────────────────────────────────────
# JSON-LD 校验
# ─────────────────────────────────────────────────────────────

def walk_jsonld(node, path="root"):
    """递归产出 (json_path, object)。"""
    if isinstance(node, dict):
        yield path, node
        for k, v in node.items():
            yield from walk_jsonld(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk_jsonld(v, f"{path}[{i}]")


def check_jsonld(report, site_root, rel, html_text, skip_assets=False):
    blocks = re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html_text, re.S | re.I)
    if not blocks:
        return []

    parsed = []
    for idx, raw in enumerate(blocks):
        try:
            data = json.loads(raw)
        except Exception as e:
            report.error(rel, "JSON-LD", f"第 {idx+1} 个 JSON-LD 块解析失败：{str(e)[:90]}")
            continue

        if not isinstance(data, dict):
            report.error(rel, "JSON-LD", f"第 {idx+1} 个 JSON-LD 顶层不是对象")
            continue

        if "@context" not in data:
            report.error(rel, "JSON-LD", f"第 {idx+1} 个 JSON-LD 缺 @context")
        if "@type" not in data:
            report.error(rel, "JSON-LD", f"第 {idx+1} 个 JSON-LD 缺 @type")

        parsed.append((idx, data))

        # 逐节点检查
        for jpath, obj in walk_jsonld(data):
            if not isinstance(obj, dict):
                continue
            otype = obj.get("@type")

            # URL 型字段：确认站内文件真的存在
            for field in ("image", "logo", "url", "contentUrl", "thumbnailUrl"):
                val = obj.get(field)
                if skip_assets:
                    continue
                if isinstance(val, str):
                    lp = to_local_path(site_root, val)
                    if lp is not None and not path_exists(site_root, lp):
                        report.error(rel, "Schema 引用",
                                     f"{jpath}.{field} 指向不存在的文件：{val}")
                elif isinstance(val, list):
                    for v in val:
                        if isinstance(v, str):
                            lp = to_local_path(site_root, v)
                            if lp is not None and not path_exists(site_root, lp):
                                report.error(rel, "Schema 引用",
                                             f"{jpath}.{field} 指向不存在的文件：{v}")

            # Product 富媒体必填项
            if otype == "Product":
                if not obj.get("image"):
                    report.error(rel, "Product schema",
                                 f"{jpath} 缺 image（Google 富媒体必填，会报严重错误）")
                offers = obj.get("offers")
                if not offers:
                    report.error(rel, "Product schema",
                                 f"{jpath} 缺 offers（Google 富媒体必填）")
                else:
                    offs = offers if isinstance(offers, list) else [offers]
                    for o in offs:
                        if not isinstance(o, dict):
                            continue
                        has_price = o.get("price") or o.get("priceSpecification")
                        if not has_price:
                            report.error(rel, "Product schema",
                                         f"{jpath}.offers 缺 price / priceSpecification"
                                         f"（会报严重错误；B2B 询价页应改用 Service）")
                        if not o.get("hasMerchantReturnPolicy"):
                            report.warn(rel, "Product schema",
                                        f"{jpath}.offers 缺 hasMerchantReturnPolicy（非严重）")
                        if not o.get("shippingDetails"):
                            report.warn(rel, "Product schema",
                                        f"{jpath}.offers 缺 shippingDetails（非严重）")
                    brand = obj.get("brand")
                    if isinstance(brand, dict) and brand.get("@type") not in ("Brand",):
                        report.warn(rel, "Product schema",
                                    f"{jpath}.brand 的 @type 是 {brand.get('@type')!r}，"
                                    f"Google 要求 Brand（非严重）")

            # FAQPage 与可见内容一致性在页面级检查里做，这里只查结构
            if otype == "FAQPage":
                me = obj.get("mainEntity")
                if not isinstance(me, list) or not me:
                    report.error(rel, "FAQPage schema", f"{jpath}.mainEntity 缺失或为空")
                else:
                    for i, q in enumerate(me):
                        if not isinstance(q, dict):
                            report.error(rel, "FAQPage schema",
                                         f"{jpath}.mainEntity[{i}] 不是对象")
                            continue
                        if not q.get("name"):
                            report.error(rel, "FAQPage schema",
                                         f"{jpath}.mainEntity[{i}] 缺 name（问题文本）")
                        ans = q.get("acceptedAnswer")
                        if not isinstance(ans, dict) or not ans.get("text"):
                            report.error(rel, "FAQPage schema",
                                         f"{jpath}.mainEntity[{i}] 缺 acceptedAnswer.text")

            if otype == "BreadcrumbList":
                items = obj.get("itemListElement")
                if not isinstance(items, list) or len(items) < 2:
                    report.warn(rel, "BreadcrumbList",
                                f"{jpath}.itemListElement 少于 2 项，面包屑意义不大")
                else:
                    for i, it in enumerate(items):
                        if not isinstance(it, dict):
                            continue
                        if it.get("position") is None:
                            report.warn(rel, "BreadcrumbList",
                                        f"{jpath}.itemListElement[{i}] 缺 position")
                        if it.get("item"):
                            lp = to_local_path(site_root, it["item"])
                            if lp is not None and not path_exists(site_root, lp):
                                report.error(rel, "BreadcrumbList",
                                             f"{jpath}.itemListElement[{i}].item "
                                             f"指向不存在的页面：{it['item']}")

    return parsed


# ─────────────────────────────────────────────────────────────
# 单页校验
# ─────────────────────────────────────────────────────────────

# 这些文件不是对外页面，不做 title / H1 / description 检查
NON_PAGE_PATTERNS = ("baidu_verify", "google", "snippets/", "404.html",
                     "case-study-template", "social-drafts/", "thank-you")


def is_non_page(rel):
    return any(pat in rel for pat in NON_PAGE_PATTERNS)


def check_page(report, site_root, f, meta_index, skip_assets=False):
    rel = str(f.relative_to(site_root))
    non_page = is_non_page(rel)
    try:
        html_text = f.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        report.error(rel, "读取", f"读文件失败：{e}")
        return

    # ---- title ----
    m = re.search(r"<title[^>]*>(.*?)</title>", html_text, re.S | re.I)
    title = norm_space(strip_tags(m.group(1))) if m else ""
    if not title:
        if not non_page:
            report.error(rel, "title", "缺 <title>")
    else:
        if len(title) < TITLE_MIN:
            report.warn(rel, "title", f"过短（{len(title)} 字符）：{title}")
        if len(title) > TITLE_MAX:
            report.warn(rel, "title", f"过长（{len(title)} 字符，SERP 会截断）：{title}")
        meta_index["titles"][title].append(rel)

    # ---- meta description ----
    m = re.search(
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']',
        html_text, re.S | re.I)
    if not m:
        m = re.search(
            r'<meta[^>]+content=["\'](.*?)["\'][^>]+name=["\']description["\']',
            html_text, re.S | re.I)
    desc = norm_space(m.group(1)) if m else ""
    if not desc:
        if not non_page:
            report.warn(rel, "description", "缺 meta description")
    else:
        if len(desc) < DESC_MIN:
            report.warn(rel, "description", f"过短（{len(desc)} 字符）")
        if len(desc) > DESC_MAX:
            report.warn(rel, "description", f"过长（{len(desc)} 字符，SERP 会截断）")
        meta_index["descs"][desc].append(rel)

    # ---- H1 ----
    h1s = re.findall(r"<h1[^>]*>(.*?)</h1>", html_text, re.S | re.I)
    if len(h1s) == 0:
        if not non_page:
            report.error(rel, "H1", "没有 H1")
    elif len(h1s) > 1:
        texts = [norm_space(strip_tags(h))[:40] for h in h1s]
        report.error(rel, "H1", f"有 {len(h1s)} 个 H1：{texts}")

    # ---- canonical ----
    m = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\'](.*?)["\']',
                  html_text, re.I)
    canonical = m.group(1).strip() if m else ""
    if not canonical:
        if not non_page:
            report.warn(rel, "canonical", "缺 canonical")
    else:
        expected = f"https://{SITE_HOST}/{rel}".replace("\\", "/")
        if rel == "index.html":
            expected = f"https://{SITE_HOST}/"
        elif rel.endswith("/index.html"):
            expected = f"https://{SITE_HOST}/{rel[:-len('index.html')]}"
        if canonical.rstrip("/") != expected.rstrip("/"):
            report.warn(rel, "canonical",
                        f"与文件路径不一致：{canonical}（期望 {expected}）")

    # ---- favicon ----
    m = re.search(r'<link[^>]+rel=["\'](?:icon|shortcut icon)["\'][^>]+href=["\'](.*?)["\']',
                  html_text, re.I)
    if not m:
        report.tally("缺 favicon 声明", rel)
    elif not skip_assets:
        lp = resolve_ref(site_root, f, m.group(1))
        if lp is not None and not path_exists(site_root, lp):
            report.error(rel, "favicon", f"声明的 favicon 不存在：{m.group(1)}")

    # ---- og / twitter ----
    if not non_page:
        for prop in ("og:title", "og:description", "og:image", "og:url"):
            if not re.search(rf'property=["\']{prop}["\']', html_text, re.I):
                report.warn(rel, "Open Graph", f"缺 {prop}")

    # ---- 图片 ----
    for m in re.finditer(r"<img\b[^>]*>", html_text, re.I):
        tag = m.group(0)
        src = re.search(r'\bsrc=["\'](.*?)["\']', tag, re.I)
        alt = re.search(r'\balt=["\'](.*?)["\']', tag, re.I)
        raw_src = src.group(1).strip() if src else ""
        if not raw_src:
            continue          # 运行时占位图（lightbox 等），alt 由 JS 填充
        if src and not skip_assets:
            lp = resolve_ref(site_root, f, src.group(1))
            if lp is not None and not path_exists(site_root, lp):
                report.error(rel, "图片", f"文件不存在：{src.group(1)}")
        if raw_src and (not alt or not alt.group(1).strip()):
            short = (src.group(1) if src else "?")[:60]
            report.warn(rel, "图片", f"缺 alt：{short}")

    # ---- 内部链接 ----
    for m in re.finditer(r'<a\b[^>]*href=["\'](.*?)["\']', html_text, re.I):
        href = m.group(1).strip()
        if not href or href.startswith(SKIP_SCHEMES) or href.startswith("#"):
            continue
        lp = resolve_ref(site_root, f, href)
        if lp is None:
            continue
        if skip_assets and lp.suffix.lower() in ASSET_EXT:
            continue
        if not path_exists(site_root, lp):
            report.error(rel, "内部链接", f"指向不存在的页面：{href}")

    # ---- footer 必须在 body 内 ----
    body_close = html_text.rfind("</body>")
    footer_open = html_text.rfind("<footer")
    if footer_open > body_close > -1:
        report.error(rel, "结构", "<footer> 在 </body> 之后")

    # ---- JSON-LD ----
    parsed = check_jsonld(report, site_root, rel, html_text, skip_assets)

    # ---- FAQPage schema 与可见 FAQ 数量对齐 ----
    visible_faq = len(re.findall(r'class=["\'][^"\']*faq-item', html_text, re.I))
    schema_faq = 0
    for idx, data in parsed:
        if data.get("@type") == "FAQPage":
            me = data.get("mainEntity")
            if isinstance(me, list):
                schema_faq = len(me)
    if schema_faq and visible_faq and schema_faq != visible_faq:
        report.warn(rel, "FAQ 一致性",
                    f"schema 有 {schema_faq} 条，页面可见 {visible_faq} 条，Google 要求一致")

    # ---- 文字量 ----
    body = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html_text, flags=re.S | re.I)
    body = re.sub(r"<[^>]+>", " ", body)
    words = len(re.findall(r"[A-Za-z][A-Za-z'\-]+", body))
    meta_index["words"][rel] = words
    if words < 300 and not non_page:
        report.warn(rel, "内容量", f"正文仅约 {words} 词，偏薄")


# ─────────────────────────────────────────────────────────────
# 站点级校验
# ─────────────────────────────────────────────────────────────

def check_site_level(report, site_root, html_files, meta_index, skip_assets=False):
    # 重复 title / description
    for t, files in meta_index["titles"].items():
        if len(files) > 1:
            report.warn(", ".join(files), "重复 title", f"{len(files)} 个页面共用：{t[:70]}")
    for d, files in meta_index["descs"].items():
        if len(files) > 1:
            report.warn(", ".join(files), "重复 description",
                        f"{len(files)} 个页面共用：{d[:70]}")

    # favicon.ico 是否在根目录
    if not (site_root / "favicon.ico").is_file() and not skip_assets:
        report.warn("favicon.ico", "站点级", "根目录没有 favicon.ico")

    # robots.txt
    robots = site_root / "robots.txt"
    if not robots.is_file():
        if not skip_assets:
            report.warn("robots.txt", "站点级", "缺 robots.txt")
    else:
        rt = robots.read_text(encoding="utf-8", errors="ignore")
        if "Sitemap:" not in rt:
            report.warn("robots.txt", "站点级", "robots.txt 里没有 Sitemap 声明")

    # sitemap 与真实文件一致性
    sm = site_root / "sitemap.xml"
    if not sm.is_file():
        report.error("sitemap.xml", "站点级", "缺 sitemap.xml")
    else:
        s = sm.read_text(encoding="utf-8", errors="ignore")
        locs = re.findall(r"<loc>(.*?)</loc>", s)
        listed = set()
        for loc in locs:
            lp = to_local_path(site_root, loc)
            if lp is None:
                continue
            resolved = lp.resolve()
            listed.add(str(resolved))
            # 目录型 URL（/products/）要对应到 products/index.html
            if resolved.is_dir():
                listed.add(str((resolved / "index.html").resolve()))
            if not path_exists(site_root, lp):
                report.error("sitemap.xml", "站点级", f"列出的 URL 不存在：{loc}")
        # 反向：站上有页面但 sitemap 没列
        for f in html_files:
            rp = str(f.resolve())
            if rp in listed:
                continue
            rel = str(f.relative_to(site_root))
            if is_non_page(rel) or "noindex" in \
                    f.read_text(encoding="utf-8", errors="ignore").lower()[:4000]:
                continue
            report.warn(rel, "sitemap", "页面存在但未列入 sitemap.xml")

        # lastmod 不能是未来
        today = __import__("datetime").date.today().isoformat()
        for lm in re.findall(r"<lastmod>(\d{4}-\d{2}-\d{2})</lastmod>", s):
            if lm > today:
                report.warn("sitemap.xml", "站点级", f"lastmod 是未来日期：{lm}")

    # 孤儿页：没有任何站内页面链向它
    inbound = Counter()
    for f in html_files:
        rel = str(f.relative_to(site_root))
        html_text = f.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r'<a\b[^>]*href=["\'](.*?)["\']', html_text, re.I):
            lp = resolve_ref(site_root, f, m.group(1))
            if lp is None:
                continue
            r = lp.resolve()
            inbound[str(r)] += 1
            if r.is_dir():
                inbound[str((r / "index.html").resolve())] += 1
    for f in html_files:
        rel = str(f.relative_to(site_root))
        if rel == "index.html" or is_non_page(rel):
            continue
        if inbound.get(str(f.resolve()), 0) == 0:
            report.warn(rel, "内链", "没有任何站内页面链接到它（孤儿页）")


# ─────────────────────────────────────────────────────────────
# 输出
# ─────────────────────────────────────────────────────────────

def print_report(report, only_errors=False):
    RED = "\033[31m" if sys.stdout.isatty() else ""
    YEL = "\033[33m" if sys.stdout.isatty() else ""
    GRN = "\033[32m" if sys.stdout.isatty() else ""
    DIM = "\033[2m" if sys.stdout.isatty() else ""
    RST = "\033[0m" if sys.stdout.isatty() else ""

    print()
    print(f"{DIM}站点校验 · {report.stats.get('site', '')}{RST}")
    print(f"{DIM}{'─'*72}{RST}")

    if report.errors:
        print(f"\n{RED}■ 错误 {len(report.errors)} 项（阻塞提交）{RST}")
        by_check = defaultdict(list)
        for e in report.errors:
            by_check[e["check"]].append(e)
        for check, items in sorted(by_check.items(), key=lambda x: -len(x[1])):
            print(f"\n  {RED}[{check}]{RST} {len(items)} 项")
            for it in items[:40]:
                print(f"    {it['file']}")
                print(f"      {it['msg']}")
            if len(items) > 40:
                print(f"    {DIM}…还有 {len(items)-40} 项{RST}")
    else:
        print(f"\n{GRN}■ 错误 0 项{RST}")

    if not only_errors:
        if report.warnings:
            print(f"\n{YEL}■ 警告 {len(report.warnings)} 项（建议修）{RST}")
            by_check = defaultdict(list)
            for w in report.warnings:
                by_check[w["check"]].append(w)
            for check, items in sorted(by_check.items(), key=lambda x: -len(x[1])):
                print(f"\n  {YEL}[{check}]{RST} {len(items)} 项")
                for it in items[:12]:
                    print(f"    {it['file']}")
                    print(f"      {it['msg']}")
                if len(items) > 12:
                    print(f"    {DIM}…还有 {len(items)-12} 项{RST}")
        else:
            print(f"\n{GRN}■ 警告 0 项{RST}")

        if report.counters:
            total = sum(len(v) for v in report.counters.values())
            print(f"\n{YEL}■ 批量问题 {total} 处（同类聚合）{RST}")
            for name, files in sorted(report.counters.items(),
                                      key=lambda x: -len(x[1])):
                print(f"  {YEL}[{name}]{RST} {len(files)} 个页面")
                print(f"    {DIM}{', '.join(files[:6])}"
                      f"{' …' if len(files) > 6 else ''}{RST}")

    print(f"\n{DIM}{'─'*72}{RST}")
    st = report.stats
    print(f"{DIM}页面 {st.get('pages',0)} · 图片引用 {st.get('images',0)} · "
          f"内链 {st.get('links',0)} · 耗时 {st.get('elapsed',0):.1f}s{RST}")
    print()


def main():
    ap = argparse.ArgumentParser(description="foshanFFE.com 站点预提交校验")
    ap.add_argument("site_dir", help="站点根目录，例如 site_work_20261029/site")
    ap.add_argument("--strict", action="store_true", help="警告也视为失败")
    ap.add_argument("--only-errors", action="store_true", help="只输出错误")
    ap.add_argument("--json", metavar="FILE", help="把结果写成 JSON")
    ap.add_argument("--skip-assets", action="store_true",
                    help="跳过图片/静态资源存在性检查（本地镜像未同步图片时用）")
    args = ap.parse_args()

    site_root = Path(args.site_dir).resolve()
    if not site_root.is_dir():
        print(f"目录不存在：{site_root}", file=sys.stderr)
        return 2

    import time
    t0 = time.time()

    report = Report()
    report.stats["site"] = str(site_root)
    html_files = collect_files(site_root, ".html")
    report.stats["pages"] = len(html_files)

    if not html_files:
        print(f"{site_root} 下没有 HTML 文件", file=sys.stderr)
        return 2

    meta_index = {"titles": defaultdict(list), "descs": defaultdict(list),
                  "words": {}}

    for f in html_files:
        check_page(report, site_root, f, meta_index, args.skip_assets)

    check_site_level(report, site_root, html_files, meta_index, args.skip_assets)

    # 统计
    img_refs = link_refs = 0
    for f in html_files:
        t = f.read_text(encoding="utf-8", errors="ignore")
        img_refs += len(re.findall(r"<img\b", t, re.I))
        link_refs += len(re.findall(r"<a\b[^>]*href=", t, re.I))
    report.stats["images"] = img_refs
    report.stats["links"] = link_refs
    report.stats["elapsed"] = time.time() - t0

    print_report(report, only_errors=args.only_errors)

    if args.json:
        Path(args.json).write_text(json.dumps({
            "site": str(site_root),
            "stats": report.stats,
            "errors": report.errors,
            "warnings": report.warnings,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"结果已写入 {args.json}")

    if report.errors:
        return 1
    if args.strict and report.warnings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
